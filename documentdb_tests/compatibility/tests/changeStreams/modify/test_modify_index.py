"""Tests for index fields in collMod Modify change-stream events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Len
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.collection_mgmt,
    pytest.mark.aggregate,
]


def _create_ttl_index(collection, ttl: int = 3600) -> None:
    """Create the TTL index used by Modify-event tests."""
    collection.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=ttl,
    )


def _ttl_event_checks(collection, requested_ttl: int, previous_ttl: int) -> dict:
    """Return common checks for one TTL Modify event."""
    return {
        "commandSucceeded": Eq(True),
        "modifyEvents": Len(1),
        "modifyEvents.0._id": Exists(),
        "modifyEvents.0._id._data": Exists(),
        "modifyEvents.0.clusterTime": Exists(),
        "modifyEvents.0.operationType": Eq("modify"),
        "modifyEvents.0.ns": Eq(
            {
                "db": collection.database.name,
                "coll": collection.name,
            }
        ),
        "modifyEvents.0.operationDescription": Eq(
            {
                "index": {
                    "name": "createdAt_1",
                    "expireAfterSeconds": Int64(requested_ttl),
                }
            }
        ),
        "modifyEvents.0.stateBeforeChange.indexOptions": Eq(
            {"expireAfterSeconds": Int64(previous_ttl)}
        ),
    }


@dataclass(frozen=True)
class HiddenKeyPatternTestCase(BaseTestCase):
    """Index type selected by keyPattern for a hidden-state CollMod."""

    index_key: dict[str, Any] = field(default_factory=dict)


# Property [Specialized Index Selection By Key Pattern]: compound, 2dsphere,
# and wildcard index key patterns resolve to their index names in the event.
HIDDEN_KEY_PATTERN_TESTS = [
    HiddenKeyPatternTestCase(
        "compound",
        index_key={"first": 1, "second": -1},
        msg=(
            "collMod should resolve a compound keyPattern to the index name "
            "and report its previous hidden state"
        ),
    ),
    HiddenKeyPatternTestCase(
        "2dsphere",
        index_key={"location": "2dsphere"},
        msg=(
            "collMod should resolve a 2dsphere keyPattern to the index name "
            "and report its previous hidden state"
        ),
    ),
    HiddenKeyPatternTestCase(
        "wildcard",
        index_key={"$**": 1},
        msg=(
            "collMod should resolve a wildcard keyPattern to the index name "
            "and report its previous hidden state"
        ),
    ),
]


# Property [Index Selection By Name]: the event reports the requested and
# previous TTL for the named index.
@pytest.mark.index
def test_modify_ttl_index_selected_by_name(collection):
    """Report the resolved index name and previous TTL when selected by name."""
    _create_ttl_index(collection)

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "name": "createdAt_1",
                    "expireAfterSeconds": 7200,
                },
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

    assertProperties(
        result,
        _ttl_event_checks(collection, 7200, 3600),
        msg="collMod by name should emit the requested and previous TTL",
        raw_res=True,
    )


# Property [Index Selection By Key Pattern]: the event resolves a key pattern
# to the selected index name and reports its TTL state.
@pytest.mark.index
def test_modify_ttl_index_selected_by_key_pattern(collection):
    """Resolve a keyPattern selector to the index name in the Modify event."""
    _create_ttl_index(collection)

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "keyPattern": {"createdAt": 1},
                    "expireAfterSeconds": 7200,
                },
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

    assertProperties(
        result,
        _ttl_event_checks(collection, 7200, 3600),
        msg="collMod by keyPattern should emit the resolved name and TTL state",
        raw_res=True,
    )


@pytest.mark.index
@pytest.mark.parametrize(
    "test_case",
    pytest_params(HIDDEN_KEY_PATTERN_TESTS),
)
def test_modify_hidden_index_selected_by_specialized_key_pattern(
    collection,
    test_case: HiddenKeyPatternTestCase,
):
    """Resolve specialized index keyPatterns in hidden-state Modify events."""
    index_name = f"{test_case.id}_idx"
    collection.create_index(
        list(test_case.index_key.items()),
        name=index_name,
    )

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "keyPattern": test_case.index_key,
                    "hidden": True,
                },
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

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationDescription.index": Eq(
                {
                    "name": index_name,
                    "hidden": True,
                }
            ),
            "modifyEvents.0.stateBeforeChange.indexOptions": Eq({"hidden": False}),
        },
        msg=test_case.msg,
        raw_res=True,
    )


# Property [TTL No-op]: requesting the existing TTL still emits exactly one
# Modify event with matching requested and previous values.
@pytest.mark.index
def test_modify_noop_ttl_emits_event(collection):
    """Emit one Modify event when the requested TTL already matches the index."""
    _create_ttl_index(collection)

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "name": "createdAt_1",
                    "expireAfterSeconds": 3600,
                },
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

    assertProperties(
        result,
        _ttl_event_checks(collection, 3600, 3600),
        msg="a TTL no-op should still emit one Modify event",
        raw_res=True,
    )


# Property [Hide Index]: hiding an index reports false as the previous hidden
# state.
@pytest.mark.index
def test_modify_hidden_reports_previous_state(collection):
    """Report the requested and previous hidden values for a hide operation."""
    collection.create_index("status", name="status_1")

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "name": "status_1",
                    "hidden": True,
                },
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

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationDescription.index": Eq({"name": "status_1", "hidden": True}),
            "modifyEvents.0.stateBeforeChange.indexOptions": Eq({"hidden": False}),
        },
        msg="hiding an index should report its previous visible state",
        raw_res=True,
    )


# Property [Unhide Index]: unhiding an index reports true as the previous
# hidden state.
@pytest.mark.index
def test_modify_unhide_reports_previous_state(collection):
    """Report the requested and previous hidden values for an unhide operation."""
    collection.create_index("status", name="status_1", hidden=True)

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "name": "status_1",
                    "hidden": False,
                },
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

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationDescription.index": Eq({"name": "status_1", "hidden": False}),
            "modifyEvents.0.stateBeforeChange.indexOptions": Eq({"hidden": True}),
        },
        msg="unhiding an index should report its previous hidden state",
        raw_res=True,
    )


# Property [Hidden No-op]: requesting the existing hidden state still emits
# exactly one Modify event.
@pytest.mark.index
def test_modify_noop_hidden_emits_event(collection):
    """Emit one Modify event when the requested hidden state is unchanged."""
    collection.create_index("status", name="status_1")

    with open_change_stream(collection) as stream:
        command_result = execute_command(
            collection,
            {
                "collMod": collection.name,
                "index": {
                    "name": "status_1",
                    "hidden": False,
                },
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

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationType": Eq("modify"),
            "modifyEvents.0.ns": Eq(
                {
                    "db": collection.database.name,
                    "coll": collection.name,
                }
            ),
        },
        msg="a hidden-state no-op should still emit one Modify event",
        raw_res=True,
    )
