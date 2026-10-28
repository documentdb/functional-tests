"""Tests for validation fields in collMod Modify change-stream events."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.changeStreams.modify.utils.modify import (
    modify_events,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len, NotExists

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.collection_mgmt,
    pytest.mark.aggregate,
]

OLD_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name"],
    }
}

NEW_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email"],
        "properties": {
            "name": {"bsonType": "string"},
            "email": {"bsonType": "string"},
        },
    }
}


def _create_validated_collection(collection, *, validation_level: str = "strict") -> None:
    """Create the fixture collection with known validation settings."""
    collection.database.create_collection(
        collection.name,
        validator=OLD_VALIDATOR,
        validationLevel=validation_level,
        validationAction="error",
    )


def _validation_before_state_checks(collection) -> dict:
    """Return checks for the validation settings present before collMod."""
    return {
        "commandSucceeded": Eq(True),
        "modifyEvents": Len(1),
        "modifyEvents.0.operationType": Eq("modify"),
        "modifyEvents.0.ns": Eq(
            {
                "db": collection.database.name,
                "coll": collection.name,
            }
        ),
        "modifyEvents.0.stateBeforeChange.collectionOptions.validator": Eq(OLD_VALIDATOR),
        "modifyEvents.0.stateBeforeChange.collectionOptions.validationAction": Eq("error"),
        "modifyEvents.0.stateBeforeChange.indexOptions": NotExists(),
    }


# Property [Validation Before-state]: changing validation reports the complete
# previous validation configuration.
def test_modify_validation_reports_before_state(collection):
    """Report all previous validation settings when changing validation."""
    _create_validated_collection(collection)

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "validator": NEW_VALIDATOR,
                "validationLevel": "moderate",
                "validationAction": "error",
            },
        )
        events = collect_until_marker(
            stream,
            collection,
            marker_fields={"name": "marker", "email": "marker@example.com"},
        )
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    checks = _validation_before_state_checks(collection)
    checks.update(
        {
            "modifyEvents.0.operationDescription": Eq(
                {
                    "validator": NEW_VALIDATOR,
                    "validationLevel": "moderate",
                    "validationAction": "error",
                }
            ),
            "modifyEvents.0.stateBeforeChange.collectionOptions.validationLevel": Eq("strict"),
        }
    )

    assertProperties(
        result,
        checks,
        msg="validation Modify events should report requested and previous settings",
        raw_res=True,
    )


# Property [Re-enable Validation]: changing validation from off to strict
# reports off as the previous level.
def test_modify_validation_off_to_strict_reports_disabled_state(collection):
    """Report validationLevel off as the state before re-enabling validation."""
    _create_validated_collection(collection, validation_level="off")

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "validationLevel": "strict",
            },
        )
        events = collect_until_marker(
            stream,
            collection,
            marker_fields={"name": "marker", "email": "marker@example.com"},
        )
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    checks = _validation_before_state_checks(collection)
    checks.update(
        {
            "modifyEvents.0.operationDescription": Eq({"validationLevel": "strict"}),
            "modifyEvents.0.stateBeforeChange.collectionOptions.validationLevel": Eq("off"),
        }
    )

    assertProperties(
        result,
        checks,
        msg="re-enabling validation should report the previous disabled level",
        raw_res=True,
    )


# Property [Remove Validator]: an empty requested validator reports the
# validator that existed before removal.
def test_modify_validator_removal_reports_previous_validator(collection):
    """Report an empty requested validator and the validator being removed."""
    _create_validated_collection(collection)

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "validator": {},
            },
        )
        events = collect_until_marker(stream, collection)
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    result["postRemovalInsert"] = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"missingRequiredName": True}],
        },
    )
    checks = _validation_before_state_checks(collection)
    checks.update(
        {
            "modifyEvents.0.operationDescription": Eq({"validator": {}}),
            "modifyEvents.0.stateBeforeChange.collectionOptions.validationLevel": Eq("strict"),
            "postRemovalInsert.ok": Eq(1.0),
            "postRemovalInsert.n": Eq(1),
        }
    )

    assertProperties(
        result,
        checks,
        msg="removing a validator should report the previous validator",
        raw_res=True,
    )


# Property [Validation No-op]: requesting the existing validation level reports
# the same requested and previous level.
def test_modify_noop_validation_reports_current_state(collection):
    """Report the current validation settings when the requested level is unchanged."""
    _create_validated_collection(collection)

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "validationLevel": "strict",
            },
        )
        events = collect_until_marker(
            stream,
            collection,
            marker_fields={"name": "marker", "email": "marker@example.com"},
        )
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    checks = _validation_before_state_checks(collection)
    checks.update(
        {
            "modifyEvents.0.operationDescription": Eq({"validationLevel": "strict"}),
            "modifyEvents.0.stateBeforeChange.collectionOptions.validationLevel": Eq("strict"),
        }
    )

    assertProperties(
        result,
        checks,
        msg="a validation no-op should report the unchanged current state",
        raw_res=True,
    )
