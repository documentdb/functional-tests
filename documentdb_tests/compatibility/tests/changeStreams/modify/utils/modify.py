"""Helpers specific to collMod Modify change-stream events."""

from __future__ import annotations

from typing import Any

from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    command_result_or_raise,
)
from documentdb_tests.framework.executor import execute_command


def modify_events(
    events: list[dict[str, Any]],
    database_name: str,
    collection_name: str,
) -> list[dict[str, Any]]:
    """Return Modify events for one collection."""
    return [
        event
        for event in events
        if event.get("operationType") == "modify"
        and event.get("ns")
        == {
            "db": database_name,
            "coll": collection_name,
        }
    ]


def index_specification(collection, index_name: str) -> dict[str, Any]:
    """Read one index specification in the shape returned by listIndexes."""
    result = command_result_or_raise(
        execute_command(
            collection,
            {"listIndexes": collection.name, "cursor": {}},
        )
    )
    for specification in result["cursor"]["firstBatch"]:
        if specification["name"] == index_name:
            return dict(specification)
    raise LookupError(f"index {index_name!r} was not returned by listIndexes")


def collection_uuid(collection):
    """Return the collection UUID reported by listCollections."""
    result = command_result_or_raise(
        execute_command(
            collection,
            {
                "listCollections": 1,
                "filter": {"name": collection.name},
            },
        )
    )
    return result["cursor"]["firstBatch"][0]["info"].get("uuid")
