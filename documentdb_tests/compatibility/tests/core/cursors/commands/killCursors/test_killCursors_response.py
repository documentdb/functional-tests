"""Tests for killCursors response structure and ordering."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Existent Cursor IDs]: a cursor ID that does not exist on
# the server is reported in cursorsNotFound and the command succeeds with
# ok 1.0.
KILLCURSORS_NONEXISTENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "nonexistent_arbitrary_id",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(999_999)],
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(999_999)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should report non-existent cursor ID in cursorsNotFound",
    ),
]

# Property [Response Order - Not Found]: input order is preserved in
# cursorsNotFound for non-existent cursor IDs.
KILLCURSORS_ORDER_NOT_FOUND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response_order_not_found",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(100), Int64(200), Int64(300), Int64(50), Int64(999)],
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(100), Int64(200), Int64(300), Int64(50), Int64(999)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should preserve input order in cursorsNotFound",
    ),
]

KILLCURSORS_RESPONSE_CMD_TESTS: list[CommandTestCase] = (
    KILLCURSORS_NONEXISTENT_TESTS + KILLCURSORS_ORDER_NOT_FOUND_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_RESPONSE_CMD_TESTS))
def test_killCursors_response_cmd(collection, test):
    """Test killCursors response structure with non-existent cursors."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Duplicate Cursor IDs]: when the same valid cursor ID appears
# multiple times, the first occurrence is killed and subsequent occurrences
# are reported in cursorsNotFound.
KILLCURSORS_DUPLICATE_IDS_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "duplicate_ids_two",
        docs=[{"_id": i} for i in range(10)],
        cursor_count=1,
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [ctx.cursors[0], ctx.cursors[0]],
        },
        expected=lambda ctx: {
            "cursorsKilled": [ctx.cursors[0]],
            "cursorsNotFound": [ctx.cursors[0]],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill first occurrence and report duplicates in cursorsNotFound",
    ),
    CursorCommandTestCase(
        "duplicate_ids_scaled",
        docs=[{"_id": i} for i in range(10)],
        cursor_count=1,
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [ctx.cursors[0]] * 100,
        },
        expected=lambda ctx: {
            "cursorsKilled": [ctx.cursors[0]],
            "cursorsNotFound": [ctx.cursors[0]] * 99,
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should handle 100 duplicates: 1 killed, 99 notFound",
    ),
]

# Property [Collection Name Matching]: the killCursors field value is not
# validated against the cursor's origin. Any valid string kills the cursor
# by ID regardless of the collection name specified.
KILLCURSORS_COLLECTION_NAME_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "wrong_collection_name",
        docs=[{"_id": i} for i in range(10)],
        cursor_count=1,
        command=lambda ctx: {
            "killCursors": "nonexistent_other_collection",
            "cursors": [ctx.cursors[0]],
        },
        expected=lambda ctx: {
            "cursorsKilled": [ctx.cursors[0]],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor regardless of collection name specified",
    ),
]

# Property [Response Structure - Order Preservation]: response order
# within cursorsKilled preserves the input order from the cursors array.
KILLCURSORS_CURSOR_ORDER_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "response_order_preservation",
        docs=[{"_id": i} for i in range(10)],
        cursor_count=5,
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": list(reversed(ctx.cursors)),
        },
        expected=lambda ctx: {
            "cursorsKilled": list(reversed(ctx.cursors)),
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should preserve input order in cursorsKilled",
    ),
]

KILLCURSORS_RESPONSE_CURSOR_TESTS: list[CursorCommandTestCase] = (
    KILLCURSORS_DUPLICATE_IDS_TESTS
    + KILLCURSORS_COLLECTION_NAME_TESTS
    + KILLCURSORS_CURSOR_ORDER_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_RESPONSE_CURSOR_TESTS))
def test_killCursors_response_cursor(database_client, collection, test):
    """Test killCursors response structure with active cursors."""
    collection = test.prepare(database_client, collection)
    cursors = open_find_cursors(collection, test.cursor_count)
    ctx = CursorCommandContext.from_collection(collection, cursors=cursors)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
