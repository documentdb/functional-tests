"""Shared $changeStream command builders and resume-token sentinels.

The builders return command documents; callers issue them with
``execute_command`` at the callsite so the database call is explicit in each
test file.
"""

from __future__ import annotations

from typing import Any


def change_stream_command(
    collection, *, pipeline, aggregate=None, **command_options
) -> dict[str, Any]:
    """Build the aggregate command document that wraps a $changeStream pipeline.

    Args:
        collection: The fixture collection the stream targets
        pipeline: The full ``[{"$changeStream": ...}]`` pipeline to run
            (required)
        aggregate: Overrides the aggregate target; defaults to the collection
            name, pass ``1`` for a database-scoped stream
        command_options: Extra keyword arguments merged as top-level command
            fields
    """
    command: dict[str, Any] = {
        "aggregate": collection.name if aggregate is None else aggregate,
        "pipeline": pipeline,
        "cursor": {},
    }
    command.update(command_options)
    return command


def get_more_command(collection, cursor_id, *, name: str | None = None) -> dict[str, Any]:
    """Build a getMore command document for an open change-stream cursor.

    Args:
        collection: The fixture collection whose name is the default namespace
        cursor_id: The id of the open change-stream cursor to advance
        name: The getMore ``collection`` field; defaults to the fixture
            collection name, set to ``$cmd.aggregate`` for a database- or
            cluster-scoped stream
    """
    return {
        "getMore": cursor_id,
        "collection": collection.name if name is None else name,
        "maxTimeMS": 500,
    }


# Placeholder for the produced resume token inside a $changeStream spec. The
# harness substitutes the token captured by ``produce_token`` before sending
# the spec, so each case can be written as a full $changeStream document.
RESUME_TOKEN = object()

# Placeholder for a source stream's operationTime, used by the mutual-exclusivity
# cases that pair a resume token with startAtOperationTime.
OPERATION_TIME = object()
