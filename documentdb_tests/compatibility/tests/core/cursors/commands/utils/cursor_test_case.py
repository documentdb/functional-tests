"""Test case and helpers for cursor command tests requiring active cursors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
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
) -> tuple[Any, ...] | Exception:
    """Open count find cursors with the given batchSize and return their IDs.

    When opening any of the find cursors fails, the engine error is returned
    instead, so the caller can forward it to the test's single assertion rather
    than indexing into it (which would raise a bare ``TypeError`` outside the
    assertion helper).
    """
    ids = []
    for _ in range(count):
        res = execute_command(collection, {"find": collection.name, "batchSize": batch_size})
        if isinstance(res, Exception):
            return res
        ids.append(res["cursor"]["id"])
    return tuple(ids)


def open_cursor(collection: Collection, find_options: dict[str, Any]) -> Any:
    """Open a cursor on ``collection`` with the given find options and return its ID.

    ``find_options`` is merged into the find command (e.g.
    ``{"tailable": True, "awaitData": True, "batchSize": 10}``). When the find
    fails, the engine error is returned instead, so the caller can forward it
    to the test's single assertion.
    """
    res = execute_command(collection, {"find": collection.name, **find_options})
    if isinstance(res, Exception):
        return res
    return res["cursor"]["id"]


KILL_CURSORS_ID_FIELDS = ("cursorsKilled", "cursorsNotFound", "cursorsAlive", "cursorsUnknown")


def label_cursor_ids(reply: Any, cursor_ids: tuple[Any, ...] | list[Any]) -> Any:
    """Replace each opened cursor ID in a killCursors reply with a stable label.

    Cursor IDs are assigned by the server and differ on every run, so a reply
    that embeds them cannot be compared against a recorded result. The ID at
    position ``i`` of ``cursor_ids`` becomes ``"cursor_<i>"`` wherever it
    appears in the four killCursors ID lists; any other ID is kept as-is.
    Field names, list lengths, order and every other field are unchanged, so
    the comparison still proves which opened cursor landed in which list.
    A non-dict reply (an engine error) is returned unchanged.
    """
    if not isinstance(reply, dict):
        return reply
    labels = {cursor_id: f"cursor_{i}" for i, cursor_id in enumerate(cursor_ids)}
    labelled = dict(reply)
    for field in KILL_CURSORS_ID_FIELDS:
        if isinstance(reply.get(field), list):
            labelled[field] = [labels.get(cursor_id, cursor_id) for cursor_id in reply[field]]
    return labelled


@dataclass(frozen=True)
class CursorCommandTestCase(CommandTestCase):
    """CommandTestCase that opens N find cursors before executing.

    The cursor IDs are available as ctx.cursors in command/expected lambdas.
    """

    cursor_count: int = 0
    find_batch_size: int = 1
