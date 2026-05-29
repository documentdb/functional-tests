"""Test case and helpers for cursor command tests requiring active cursors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.executor import execute_command


@dataclass(frozen=True)
class CursorCommandContext(CommandContext):
    """CommandContext extended with cursor IDs opened during setup."""

    cursors: tuple[Any, ...] = ()

    @classmethod
    def from_collection(
        cls, collection: Collection, *, cursors: tuple[Any, ...] = ()
    ) -> CursorCommandContext:
        """Create context with optional cursor IDs."""
        base = CommandContext.from_collection(collection)
        return cls(
            collection=base.collection,
            database=base.database,
            namespace=base.namespace,
            uuids=base.uuids,
            cursors=cursors,
        )


def open_find_cursors(
    collection: Collection, count: int, *, batch_size: int = 1
) -> tuple[Any, ...]:
    """Open count find cursors with the given batchSize and return their IDs."""
    ids = []
    for _ in range(count):
        res = execute_command(collection, {"find": collection.name, "batchSize": batch_size})
        ids.append(res["cursor"]["id"])
    return tuple(ids)


def open_cursor(collection: Collection, find_options: dict[str, Any]) -> Any:
    """Open a cursor on ``collection`` with the given find options and return its ID.

    ``find_options`` is merged into the find command (e.g.
    ``{"tailable": True, "awaitData": True, "batchSize": 10}``).
    """
    res = execute_command(collection, {"find": collection.name, **find_options})
    return res["cursor"]["id"]


@dataclass(frozen=True)
class CursorCommandTestCase(CommandTestCase):
    """CommandTestCase that opens N find cursors before executing.

    The cursor IDs are available as ctx.cursors in command/expected lambdas.
    """

    cursor_count: int = 0
    find_batch_size: int = 1
