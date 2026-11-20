"""Tests for collMod Modify event scope, visibility, and resume behavior."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.changeStreams.modify.utils.modify import (
    collection_uuid,
    index_specification,
    modify_events,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import (
    Eq,
    Gte,
    IsType,
    Len,
    Lte,
    Ne,
    NotExists,
)

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.collection_mgmt,
    pytest.mark.aggregate,
]


def _create_ttl_index(collection) -> None:
    """Create the TTL index used by stream behavior tests."""
    collection.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=3600,
    )


def _ttl_command(collection, ttl: int) -> dict:
    """Build a collMod command that changes the fixture TTL index."""
    return {
        "collMod": collection.name,
        "index": {
            "name": "createdAt_1",
            "expireAfterSeconds": ttl,
        },
    }


def _command_succeeded(result) -> bool:
    """Return whether execute_command returned a successful command document."""
    return not isinstance(result, Exception) and result.get("ok") == 1


# Property [Stream Scope]: collection-, database-, and cluster-scoped streams
# return the same Modify event.
@pytest.mark.index
@pytest.mark.parametrize(
    "scope",
    ["collection", "database", "cluster"],
    ids=["collection_scope", "database_scope", "cluster_scope"],
)
def test_modify_event_visible_at_each_scope(collection, scope):
    """Return the same Modify event at collection, database, and cluster scope."""
    _create_ttl_index(collection)
    expected_collection_uuid = collection_uuid(collection)

    with open_change_stream(collection, scope=scope) as stream:
        command_result = execute_command(
            collection,
            _ttl_command(collection, 7200),
        )
        events = collect_until_marker(stream, collection)
    matching_events = modify_events(
        events,
        collection.database.name,
        collection.name,
    )
    matching_event = matching_events[0] if matching_events else {}
    wall_time = matching_event.get("wallTime")
    result = {
        "commandSucceeded": _command_succeeded(command_result),
        "modifyEvents": matching_events,
        "listCollectionsUUID": expected_collection_uuid,
        "collectionUuidMatches": (
            expected_collection_uuid is not None
            and matching_event.get("collectionUUID") == expected_collection_uuid
        ),
        "beforeStateUuidMatches": (
            expected_collection_uuid is not None
            and matching_event.get("stateBeforeChange", {}).get("collectionOptions", {}).get("uuid")
            == expected_collection_uuid
        ),
        "wallTimeIsTimezoneAware": (
            isinstance(wall_time, datetime)
            and wall_time.tzinfo is not None
            and wall_time.utcoffset() is not None
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
            "modifyEvents.0.operationDescription.index.expireAfterSeconds": Eq(Int64(7200)),
            "modifyEvents.0.stateBeforeChange.indexOptions.expireAfterSeconds": Eq(Int64(3600)),
            "modifyEvents.0._id": IsType("object"),
            "modifyEvents.0._id._data": IsType("string"),
            "modifyEvents.0.clusterTime": IsType("timestamp"),
            "modifyEvents.0.collectionUUID": IsType("binData"),
            "modifyEvents.0.wallTime": IsType("date"),
            "modifyEvents.0.documentKey": NotExists(),
            "modifyEvents.0.fullDocument": NotExists(),
            "modifyEvents.0.lsid": NotExists(),
            "modifyEvents.0.txnNumber": NotExists(),
            "listCollectionsUUID": IsType("binData"),
            "collectionUuidMatches": Eq(True),
            "beforeStateUuidMatches": Eq(True),
            "wallTimeIsTimezoneAware": Eq(True),
        },
        msg=f"a {scope}-scoped stream should return the collMod Modify event",
        raw_res=True,
    )


# Property [Expanded Event Visibility]: omitting showExpandedEvents suppresses
# the Modify event without suppressing the collMod command.
@pytest.mark.index
@pytest.mark.parametrize(
    "show_expanded",
    [False, None],
    ids=["false", "omitted"],
)
def test_modify_suppressed_without_expanded_events(
    collection,
    show_expanded,
):
    """Suppress a Modify event when expanded events are false or omitted."""
    _create_ttl_index(collection)

    with open_change_stream(
        collection,
        scope="database",
        show_expanded_events=show_expanded,
    ) as stream:
        command_result = execute_command(
            collection,
            _ttl_command(collection, 7200),
        )
        events = collect_until_marker(stream, collection)
    result = {
        "commandSucceeded": _command_succeeded(command_result),
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
            "finalTtl": [Gte(7200), Lte(7200)],
        },
        msg=("showExpandedEvents false or omitted should suppress the " "Modify event"),
        raw_res=True,
    )


# Property [Resume After Modify]: resuming from one Modify token returns only a
# later Modify event.
@pytest.mark.index
def test_modify_resume_after_returns_later_event(collection):
    """Resume after one Modify token and return only the later modification."""
    _create_ttl_index(collection)
    with open_change_stream(collection) as stream:
        first_command_result = execute_command(
            collection,
            _ttl_command(collection, 7200),
        )
        first_events = collect_until_marker(stream, collection)
    first_modify_events = modify_events(
        first_events,
        collection.database.name,
        collection.name,
    )
    first_token = first_modify_events[0]["_id"]

    with open_change_stream(
        collection,
        resume_after=first_token,
    ) as resumed:
        command_result = execute_command(
            collection,
            _ttl_command(collection, 9000),
        )
        resumed_events = collect_until_marker(resumed, collection)
    result = {
        "firstCommandSucceeded": _command_succeeded(first_command_result),
        "firstModifyEvents": first_modify_events,
        "secondCommandSucceeded": _command_succeeded(command_result),
        "modifyEvents": modify_events(
            resumed_events,
            collection.database.name,
            collection.name,
        ),
    }

    assertProperties(
        result,
        {
            "firstCommandSucceeded": Eq(True),
            "firstModifyEvents": Len(1),
            "secondCommandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0._id": Ne(first_token),
            "modifyEvents.0.operationDescription.index.expireAfterSeconds": [
                Gte(9000),
                Lte(9000),
            ],
            "modifyEvents.0.stateBeforeChange.indexOptions.expireAfterSeconds": [
                Gte(7200),
                Lte(7200),
            ],
        },
        msg="resumeAfter a Modify token should return only the later Modify event",
        raw_res=True,
    )


# Property [Start After Modify]: starting after one Modify token returns only a
# later Modify event.
@pytest.mark.index
def test_modify_start_after_returns_later_event(collection):
    """Start after one Modify token and return only the later modification."""
    _create_ttl_index(collection)
    with open_change_stream(collection) as stream:
        first_command_result = execute_command(
            collection,
            _ttl_command(collection, 7200),
        )
        first_events = collect_until_marker(stream, collection)
    first_modify_events = modify_events(
        first_events,
        collection.database.name,
        collection.name,
    )
    first_token = first_modify_events[0]["_id"]

    with open_change_stream(
        collection,
        start_after=first_token,
    ) as resumed:
        second_command_result = execute_command(
            collection,
            _ttl_command(collection, 9000),
        )
        resumed_events = collect_until_marker(resumed, collection)
    result = {
        "firstCommandSucceeded": _command_succeeded(first_command_result),
        "firstModifyEvents": first_modify_events,
        "secondCommandSucceeded": _command_succeeded(second_command_result),
        "modifyEvents": modify_events(
            resumed_events,
            collection.database.name,
            collection.name,
        ),
    }

    assertProperties(
        result,
        {
            "firstCommandSucceeded": Eq(True),
            "firstModifyEvents": Len(1),
            "secondCommandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0._id": Ne(first_token),
            "modifyEvents.0.operationDescription.index.expireAfterSeconds": [
                Gte(9000),
                Lte(9000),
            ],
            "modifyEvents.0.stateBeforeChange.indexOptions.expireAfterSeconds": [
                Gte(7200),
                Lte(7200),
            ],
        },
        msg="startAfter a Modify token should return only the later Modify event",
        raw_res=True,
    )


# Property [Start At Operation Time]: starting before a collMod replays its
# Modify event.
@pytest.mark.index
def test_modify_start_at_operation_time_replays_event(collection):
    """Replay a Modify event from an operation time before the collMod."""
    _create_ttl_index(collection)

    with open_change_stream(collection) as anchor:
        anchor_events = collect_until_marker(anchor, collection)
        start_time = next(
            event["clusterTime"]
            for event in anchor_events
            if event.get("operationType") == "insert"
            and event.get("ns")
            == {
                "db": collection.database.name,
                "coll": collection.name,
            }
        )

    command_result = execute_command(
        collection,
        _ttl_command(collection, 7200),
    )

    with open_change_stream(
        collection,
        start_at_operation_time=start_time,
    ) as replay:
        replayed_events = collect_until_marker(replay, collection)
    result = {
        "commandSucceeded": _command_succeeded(command_result),
        "modifyEvents": modify_events(
            replayed_events,
            collection.database.name,
            collection.name,
        ),
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationDescription.index.expireAfterSeconds": [
                Gte(7200),
                Lte(7200),
            ],
            "modifyEvents.0.stateBeforeChange.indexOptions.expireAfterSeconds": [
                Gte(3600),
                Lte(3600),
            ],
        },
        msg="startAtOperationTime should replay the later Modify event",
        raw_res=True,
    )
