"""Tests for failed collMod commands and Modify event suppression."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.changeStreams.modify.utils.modify import (
    index_specification,
    modify_events,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.error_codes import (
    INDEX_NOT_FOUND_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.collection_mgmt,
    pytest.mark.aggregate,
]


# Property [Missing Index]: a missing target returns index-not-found and emits
# no Modify event, without changing the existing TTL index.
@pytest.mark.index
def test_missing_index_collmod_emits_no_modify_event(collection):
    """Fail without an event or a change to the existing TTL index."""
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
                    "name": "missing_1",
                    "expireAfterSeconds": 7200,
                },
            },
        )
        events = collect_until_marker(stream, collection)
    result = {
        "commandCode": getattr(command_result, "code", None),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
        "existingIndexTtl": index_specification(
            collection,
            "createdAt_1",
        )["expireAfterSeconds"],
    }

    assertProperties(
        result,
        {
            "commandCode": Eq(INDEX_NOT_FOUND_ERROR),
            "modifyEvents": Len(0),
            "existingIndexTtl": Eq(3600),
        },
        msg="a missing index should fail without an event or changing the existing TTL",
        raw_res=True,
    )


# Property [Invalid Option]: an unrecognized collMod option fails and emits no
# Modify event, without changing the existing TTL index.
def test_invalid_collmod_emits_no_modify_event(collection):
    """Fail without an event or a change to the existing TTL index."""
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
                "unknownModifyOption": True,
            },
        )
        events = collect_until_marker(stream, collection)
    result = {
        "commandCode": getattr(command_result, "code", None),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
        "existingIndexTtl": index_specification(
            collection,
            "createdAt_1",
        )["expireAfterSeconds"],
    }

    assertProperties(
        result,
        {
            "commandCode": Eq(UNRECOGNIZED_COMMAND_FIELD_ERROR),
            "modifyEvents": Len(0),
            "existingIndexTtl": Eq(3600),
        },
        msg="an invalid collMod should fail without an event or changing the existing TTL",
        raw_res=True,
    )


# Property [Collection Drop Side Effect]: dropping a collection emits its drop
# event without a dependent Modify event.
def test_collection_drop_emits_no_dependent_modify_event(
    database_client,
    collection,
):
    """Do not emit a Modify event when a collection is dropped."""
    collection.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=3600,
    )
    marker_collection = database_client[f"{collection.name}_marker"]
    marker_collection.insert_one({"setup": True})

    with open_change_stream(marker_collection, scope="database") as stream:
        command_result = execute_command(
            collection,
            {"drop": collection.name},
        )
        events = collect_until_marker(stream, marker_collection)

    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "collectionDropEvents": [
            event
            for event in events
            if event.get("operationType") == "drop"
            and event.get("ns")
            == {
                "db": database_client.name,
                "coll": collection.name,
            }
        ],
        "modifyEvents": modify_events(
            events,
            database_client.name,
            collection.name,
        ),
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "collectionDropEvents": Len(1),
            "modifyEvents": Len(0),
        },
        msg="dropping a collection should not emit a dependent Modify event",
        raw_res=True,
    )


# Property [Different Namespace]: a collection-scoped stream does not receive
# another collection's Modify event.
@pytest.mark.index
def test_other_collection_stream_receives_no_modify_event(collection):
    """Do not deliver a Modify event to a different collection stream."""
    other_collection = collection.database[f"{collection.name}_other"]
    collection.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=3600,
    )
    other_collection.insert_one({"setup": True})

    with open_change_stream(other_collection) as stream:
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
        events = collect_until_marker(stream, other_collection)

    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            collection.name,
        ),
        "finalTtl": index_specification(
            collection,
            "createdAt_1",
        )["expireAfterSeconds"],
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(0),
            "finalTtl": Eq(7200),
        },
        msg="a collection stream should not receive another collection's Modify event",
        raw_res=True,
    )
