"""Tests for resuming change streams across dropIndexes events."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.changeStreams.dropIndexes.utils.drop_indexes import (
    collect_until_marker,
    drop_index_events,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.aggregate,
    pytest.mark.index,
]


def _create_indexes(collection, names):
    """Create ascending indexes whose field names come from their index names."""
    collection.insert_one({"_id": 1, **{name.split("_", 1)[0]: 1 for name in names}})
    for name in names:
        collection.create_index(name.split("_", 1)[0], name=name)


def _event_names(events, collection):
    """Return the dropped index names for one test collection."""
    return [
        event["operationDescription"]["indexes"][0]["name"]
        for event in drop_index_events(events, collection.database.name, collection.name)
    ]


def test_dropIndexes_resume_after_returns_only_later_event(collection):
    """Resume after one index drop and return only the later dropIndexes event."""
    _create_indexes(collection, ["a_1", "b_1"])

    with open_change_stream(collection, scope="database") as stream:
        first_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "a_1"},
        )
        first_events = collect_until_marker(stream, collection)
        first_drops = drop_index_events(first_events, collection.database.name, collection.name)
        token = first_drops[0]["_id"]

    with open_change_stream(collection, scope="database", resume_after=token) as resumed:
        second_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "b_1"},
        )
        resumed_events = collect_until_marker(resumed, collection)

    summary = {
        "first_ok": first_result.get("ok") if isinstance(first_result, dict) else None,
        "first_names": _event_names(first_events, collection),
        "second_ok": second_result.get("ok") if isinstance(second_result, dict) else None,
        "resumed_names": _event_names(resumed_events, collection),
    }
    assertSuccess(
        summary,
        {
            "first_ok": 1.0,
            "first_names": ["a_1"],
            "second_ok": 1.0,
            "resumed_names": ["b_1"],
        },
        msg="resumeAfter should return only the dropIndexes event after the saved token",
        raw_res=True,
    )


def test_dropIndexes_resume_after_star_returns_remaining_events(collection):
    """Resume after event two of five wildcard drops and replay events three to five."""
    index_names = ["a_1", "b_1", "c_1", "d_1", "e_1"]
    _create_indexes(collection, index_names)

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "*"},
        )
        events = collect_until_marker(stream, collection)
        drops = drop_index_events(events, collection.database.name, collection.name)
        second_token = drops[1]["_id"]
        expected_remaining = sorted(
            event["operationDescription"]["indexes"][0]["name"] for event in drops[2:]
        )

    with open_change_stream(collection, scope="database", resume_after=second_token) as resumed:
        replayed_events = collect_until_marker(resumed, collection)

    summary = {
        "drop_ok": drop_result.get("ok") if isinstance(drop_result, dict) else None,
        "initial_count": len(drops),
        "expected_remaining": expected_remaining,
        "replayed_names": sorted(_event_names(replayed_events, collection)),
    }
    assertSuccess(
        summary,
        {
            "drop_ok": 1.0,
            "initial_count": 5,
            "expected_remaining": expected_remaining,
            "replayed_names": expected_remaining,
        },
        msg="resumeAfter should replay only wildcard-drop events after the saved token",
        raw_res=True,
    )


def test_dropIndexes_start_at_operation_time_replays_star_events(collection):
    """Start before a wildcard drop and replay every resulting dropIndexes event."""
    _create_indexes(collection, ["a_1", "b_1"])

    with open_change_stream(collection, scope="database") as anchor:
        anchor_events = collect_until_marker(anchor, collection)
        start_time = next(
            event["clusterTime"]
            for event in anchor_events
            if event.get("operationType") == "insert"
            and event.get("ns", {}).get("db") == collection.database.name
            and event.get("ns", {}).get("coll") == collection.name
        )

    drop_result = execute_command(
        collection,
        {"dropIndexes": collection.name, "index": "*"},
    )

    with open_change_stream(
        collection,
        scope="database",
        start_at_operation_time=start_time,
    ) as replay:
        replayed_events = collect_until_marker(replay, collection)

    summary = {
        "drop_ok": drop_result.get("ok") if isinstance(drop_result, dict) else None,
        "replayed_names": sorted(_event_names(replayed_events, collection)),
    }
    assertSuccess(
        summary,
        {"drop_ok": 1.0, "replayed_names": ["a_1", "b_1"]},
        msg="startAtOperationTime should replay every wildcard dropIndexes event",
        raw_res=True,
    )
