"""Tests for combined collMod Modify change-stream event fields."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.changeStreams.modify.utils.modify import (
    modify_events,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Gte, Len, Lte

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
    }
}


# Property [Combined Index Options]: one event contains both requested and
# previous TTL and hidden values.
@pytest.mark.index
def test_modify_combines_ttl_and_hidden(collection):
    """Emit one event containing both TTL and hidden before-state."""
    collection.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=3600,
        hidden=True,
    )

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "name": "createdAt_1",
                    "expireAfterSeconds": 7200,
                    "hidden": False,
                },
            },
        )
        events = collect_until_marker(stream, collection)
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "command": command_result if isinstance(command_result, dict) else {},
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "command.expireAfterSeconds_old": [Gte(3600), Lte(3600)],
            "command.expireAfterSeconds_new": [Gte(7200), Lte(7200)],
            "command.hidden_old": Eq(True),
            "command.hidden_new": Eq(False),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationDescription.index": Eq(
                {
                    "name": "createdAt_1",
                    "expireAfterSeconds": Int64(7200),
                    "hidden": False,
                }
            ),
            "modifyEvents.0.stateBeforeChange.indexOptions": Eq(
                {
                    "expireAfterSeconds": Int64(3600),
                    "hidden": True,
                }
            ),
        },
        msg="one Modify event should combine TTL and hidden index changes",
        raw_res=True,
    )


# Property [Combined Index And Validation]: one event contains all requested
# index and validation fields and their previous state.
@pytest.mark.index
def test_modify_combines_index_and_validation_fields(collection):
    """Emit one event containing index and validation requested and previous state."""
    collection.database.create_collection(
        collection.name,
        validator=OLD_VALIDATOR,
        validationLevel="strict",
        validationAction="error",
    )
    collection.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=3600,
    )

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "name": "createdAt_1",
                    "expireAfterSeconds": 7200,
                },
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

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationDescription": Eq(
                {
                    "index": {
                        "name": "createdAt_1",
                        "expireAfterSeconds": Int64(7200),
                    },
                    "validator": NEW_VALIDATOR,
                    "validationLevel": "moderate",
                    "validationAction": "error",
                }
            ),
            "modifyEvents.0.stateBeforeChange.indexOptions": Eq(
                {"expireAfterSeconds": Int64(3600)}
            ),
            "modifyEvents.0.stateBeforeChange.collectionOptions.validator": Eq(OLD_VALIDATOR),
            "modifyEvents.0.stateBeforeChange.collectionOptions.validationLevel": Eq("strict"),
            "modifyEvents.0.stateBeforeChange.collectionOptions.validationAction": Eq("error"),
        },
        msg="one Modify event should combine index and validation changes",
        raw_res=True,
    )
