"""Shared change-stream cursor and event collection helpers."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from bson import ObjectId

from documentdb_tests.framework.executor import execute_command

GET_MORE_TIMEOUT_MS = 500
MARKER_TIMEOUT_SECONDS = 30


@dataclass
class ChangeStreamCursor:
    """State required to read and close a change-stream cursor."""

    command_collection: Any
    cursor_id: int
    cursor_collection: str
    initial_events: list[dict[str, Any]]


def command_result_or_raise(result: Any) -> dict[str, Any]:
    """Return a successful command result or raise the returned exception."""
    if isinstance(result, Exception):
        raise result
    if not isinstance(result, dict):
        raise TypeError(f"expected a command result document, got {type(result)!r}")
    return result


def _stream_target(collection, scope: str):
    """Return the command collection and aggregate target for a watch scope."""
    if scope == "collection":
        return collection, collection.name, collection.name, {}
    if scope == "database":
        return collection, 1, "$cmd.aggregate", {}
    if scope == "cluster":
        admin_collection = collection.database.client.admin[collection.name]
        return admin_collection, 1, "$cmd.aggregate", {"allChangesForCluster": True}
    raise ValueError(f"unsupported change-stream scope: {scope}")


@contextmanager
def open_change_stream(
    collection,
    *,
    scope: str = "collection",
    show_expanded_events: bool | None = True,
    resume_after: dict[str, Any] | None = None,
    start_after: dict[str, Any] | None = None,
    start_at_operation_time: Any = None,
) -> Iterator[ChangeStreamCursor]:
    """Open a change stream and close its cursor when the test finishes."""
    command_collection, aggregate, cursor_collection, spec = _stream_target(collection, scope)
    if show_expanded_events is not None:
        spec["showExpandedEvents"] = show_expanded_events
    if resume_after is not None:
        spec["resumeAfter"] = resume_after
    if start_after is not None:
        spec["startAfter"] = start_after
    if start_at_operation_time is not None:
        spec["startAtOperationTime"] = start_at_operation_time

    opened = command_result_or_raise(
        execute_command(
            command_collection,
            {
                "aggregate": aggregate,
                "pipeline": [{"$changeStream": spec}],
                "cursor": {},
            },
        )
    )
    cursor = ChangeStreamCursor(
        command_collection=command_collection,
        cursor_id=opened["cursor"]["id"],
        cursor_collection=cursor_collection,
        initial_events=list(opened["cursor"].get("firstBatch", [])),
    )
    try:
        yield cursor
    finally:
        if cursor.cursor_id:
            execute_command(
                cursor.command_collection,
                {
                    "killCursors": cursor.cursor_collection,
                    "cursors": [cursor.cursor_id],
                },
            )


def collect_until_marker(
    stream: ChangeStreamCursor,
    marker_collection,
    *,
    marker_fields: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Insert a marker document and return all events through that insert."""
    marker = ObjectId()
    marker_collection.insert_one(
        {
            **(marker_fields or {}),
            "_id": marker,
            "change_stream_test_marker": True,
        }
    )

    events = list(stream.initial_events)
    stream.initial_events.clear()
    deadline = time.monotonic() + MARKER_TIMEOUT_SECONDS

    while not any(
        event.get("operationType") == "insert"
        and event.get("ns", {}).get("db") == marker_collection.database.name
        and event.get("ns", {}).get("coll") == marker_collection.name
        and event.get("documentKey", {}).get("_id") == marker
        for event in events
    ):
        if time.monotonic() >= deadline:
            raise TimeoutError("change stream did not reach the marker document")

        result = command_result_or_raise(
            execute_command(
                stream.command_collection,
                {
                    "getMore": stream.cursor_id,
                    "collection": stream.cursor_collection,
                    "maxTimeMS": GET_MORE_TIMEOUT_MS,
                },
            )
        )
        events.extend(result["cursor"].get("nextBatch", []))
        stream.cursor_id = result["cursor"]["id"]

    return events
