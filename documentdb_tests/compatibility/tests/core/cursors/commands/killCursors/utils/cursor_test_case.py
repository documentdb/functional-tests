"""Test case and helpers for killCursors tests requiring active cursors."""

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


def open_find_cursors(collection: Collection, count: int) -> tuple[Any, ...]:
    """Open count find cursors with batchSize 1 and return their IDs."""
    ids = []
    for _ in range(count):
        res = execute_command(collection, {"find": collection.name, "batchSize": 1})
        ids.append(res["cursor"]["id"])
    return tuple(ids)


@dataclass(frozen=True)
class CursorCommandTestCase(CommandTestCase):
    """CommandTestCase that opens N find cursors before executing.

    The cursor IDs are available as ctx.cursors in command/expected lambdas.
    """

    cursor_count: int = 0
