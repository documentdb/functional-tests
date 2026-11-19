"""Helpers specific to dropIndexes change-stream tests."""

from __future__ import annotations

from typing import Any

from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    command_result_or_raise,
)
from documentdb_tests.framework.executor import execute_command


def drop_index_events(events, database_name: str, collection_name: str):
    """Return dropIndexes events for one collection."""
    return [
        event
        for event in events
        if event.get("operationType") == "dropIndexes"
        and event.get("ns") == {"db": database_name, "coll": collection_name}
    ]


def index_specification(collection, index_name: str) -> dict[str, Any]:
    """Read one index specification in the same shape returned by listIndexes."""
    result = command_result_or_raise(
        execute_command(
            collection,
            {"listIndexes": collection.name, "cursor": {}},
        )
    )
    for specification in result["cursor"]["firstBatch"]:
        if specification["name"] == index_name:
            specification = dict(specification)
            specification.pop("ns", None)
            return specification
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
