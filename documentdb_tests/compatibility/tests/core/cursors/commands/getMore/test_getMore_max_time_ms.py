"""Tests for getMore maxTimeMS behavior."""

from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_cursor,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte, Len
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT32_MAX,
)

# Property [maxTimeMS Accepted Values]: numeric values that represent a whole
# number in the range 0 to 2147483647 are accepted as maxTimeMS on awaitData
# tailable cursors.
GETMORE_MAX_TIME_MS_ACCEPTED_TESTS: list[CursorCommandTestCase] = [
    # Negative zero variants accepted as 0.
    CursorCommandTestCase(
        "accepted_double_neg_zero",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept double -0.0 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "accepted_decimal_neg_zero",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept Decimal128 -0 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "accepted_decimal_neg_zero_dot",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": Decimal128("-0.0"),
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept Decimal128 -0.0 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "accepted_decimal_neg_zero_exp",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": Decimal128("-0E+10"),
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept Decimal128 -0E+10 as maxTimeMS",
    ),
    # Decimal128 with trailing zeros accepted when value is whole number in range.
    CursorCommandTestCase(
        "accepted_decimal_0_0",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": Decimal128("0.0"),
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept Decimal128 0.0 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "accepted_decimal_1_0",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": DECIMAL128_TRAILING_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept Decimal128 1.0 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "accepted_decimal_1_00",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": Decimal128("1.00"),
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept Decimal128 1.00 as maxTimeMS",
    ),
    # Decimal128 in scientific notation accepted when result is whole number in range.
    CursorCommandTestCase(
        "accepted_decimal_1e2",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": Decimal128("1E+2"),
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept Decimal128 1E+2 as maxTimeMS",
    ),
    # Whole-number doubles accepted.
    CursorCommandTestCase(
        "accepted_double_0_0",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": DOUBLE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept double 0.0 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "accepted_double_1_0",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": 1.0,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept double 1.0 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "accepted_double_100_0",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": 100.0,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept double 100.0 as maxTimeMS",
    ),
    # Range boundaries: 0 and max int32.
    CursorCommandTestCase(
        "accepted_zero",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": 0,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept maxTimeMS=0",
    ),
    CursorCommandTestCase(
        "accepted_int32_max",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": INT32_MAX,
        },
        expected={"ok": Eq(1.0)},
        msg="getMore should accept maxTimeMS at max int32",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_MAX_TIME_MS_ACCEPTED_TESTS))
def test_getMore_max_time_ms_accepted(collection, test_case: CursorCommandTestCase):
    """Test getMore maxTimeMS accepted values on awaitData tailable cursor."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 2})
    ctx = CursorCommandContext.from_collection(capped, cursors=(cursor_id,))
    result = execute_command(collection, test_case.build_command(ctx))
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [maxTimeMS Semantic Constraint - Non-Tailable]: maxTimeMS on
# non-tailable cursors produces BAD_VALUE_ERROR.
GETMORE_MAX_TIME_MS_SEMANTIC_NON_TAILABLE_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "semantic_non_tailable",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": 100,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject maxTimeMS on a non-tailable cursor",
    ),
    CursorCommandTestCase(
        "semantic_zero_non_tailable",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": 0,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject maxTimeMS=0 on a non-tailable cursor",
    ),
]


@pytest.mark.parametrize(
    "test_case", pytest_params(GETMORE_MAX_TIME_MS_SEMANTIC_NON_TAILABLE_TESTS)
)
def test_getMore_max_time_ms_semantic_non_tailable(collection, test_case: CursorCommandTestCase):
    """Test getMore rejects maxTimeMS on non-tailable cursors."""
    collection.insert_many([{"_id": i} for i in range(5)])
    cursors = open_find_cursors(
        collection, test_case.cursor_count, batch_size=test_case.find_batch_size
    )
    ctx = CursorCommandContext.from_collection(collection, cursors=cursors)
    result = execute_command(collection, test_case.build_command(ctx))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [maxTimeMS Semantic Constraint - Tailable Without AwaitData]: maxTimeMS
# on tailable cursors without awaitData produces BAD_VALUE_ERROR.
GETMORE_MAX_TIME_MS_SEMANTIC_TAILABLE_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "semantic_tailable_no_await",
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "maxTimeMS": 100,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject maxTimeMS on a tailable cursor without awaitData",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_MAX_TIME_MS_SEMANTIC_TAILABLE_TESTS))
def test_getMore_max_time_ms_semantic_tailable(collection, test_case: CursorCommandTestCase):
    """Test getMore rejects maxTimeMS on tailable cursors without awaitData."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "batchSize": 2})
    ctx = CursorCommandContext.from_collection(capped, cursors=(cursor_id,))
    result = execute_command(collection, test_case.build_command(ctx))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [maxTimeMS Null Bypass]: maxTimeMS=null bypasses the semantic check
# that otherwise rejects maxTimeMS on non-awaitData cursors.
def test_getMore_max_time_ms_null_bypasses_semantic_check(collection):
    """Test getMore maxTimeMS=null bypasses the non-awaitData semantic check."""
    collection.insert_many([{"_id": i} for i in range(5)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "maxTimeMS": None},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg="getMore should succeed with maxTimeMS=null on non-awaitData cursor",
        raw_res=True,
    )


# Property [maxTimeMS Per-Call]: maxTimeMS is accepted independently on each
# successive getMore call on the same cursor.
def test_getMore_max_time_ms_varies_between_calls(collection):
    """Test getMore accepts a different maxTimeMS on each successive call on the same cursor."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 2})
    r1 = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 50},
    )
    cursor_id2 = r1["cursor"]["id"]
    r2 = execute_command(
        collection,
        {"getMore": cursor_id2, "collection": capped.name, "maxTimeMS": 200},
    )
    assertResult(
        r2,
        expected={"ok": Eq(1.0)},
        msg="getMore should accept a different maxTimeMS on a successive call",
        raw_res=True,
    )


# Property [maxTimeMS With Data]: getMore accepts maxTimeMS and returns the
# available data when documents are present.
def test_getMore_max_time_ms_returns_immediately_with_data(collection):
    """Test getMore accepts maxTimeMS and returns available data."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 2})
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 5_000},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3)}},
        msg="getMore should accept maxTimeMS and return available data",
        raw_res=True,
    )


# Property [maxTimeMS No-Data Behavior]: on a tailable awaitData cursor with no
# data available, maxTimeMS returns an empty batch and keeps the cursor open.
def test_getMore_max_time_ms_no_data_empty_batch(collection):
    """Test getMore with maxTimeMS returns empty batch and keeps cursor open when no data."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 10})
    execute_command(collection, {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 0})
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 0},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Eq([]), "id": Gte(1)}},
        msg="getMore with maxTimeMS should return empty batch and keep cursor open when no data",
        raw_res=True,
    )


# Property [maxTimeMS Wait Elapsed Retains Cursor]: a getMore whose awaitData
# maxTimeMS wait elapses with no new data keeps the tailable cursor open for
# subsequent getMore calls.
def test_getMore_max_time_ms_wait_elapsed_retains_cursor(collection):
    """Test a getMore whose awaitData wait elapses keeps the cursor open for later calls."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 10})
    # maxTimeMS=0 returns immediately (no wait), positioning the cursor at the tail.
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 0},
    )
    cursor_id = result["cursor"]["id"]
    # maxTimeMS=100 lets the awaitData wait window elapse with no new data; the
    # cursor must remain open afterward.
    result2 = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 100},
    )
    assertResult(
        result2,
        expected={"ok": Eq(1.0), "cursor": {"id": Gte(1)}},
        msg="getMore should keep a tailable cursor open after the awaitData wait elapses",
        raw_res=True,
    )


# Property [maxTimeMS Omitted AwaitData]: getMore succeeds when maxTimeMS is
# omitted on an awaitData tailable cursor.
def test_getMore_missing_max_time_ms_await_data(collection):
    """Test getMore succeeds with maxTimeMS omitted on awaitData tailable cursor."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 2})
    result = execute_command(collection, {"getMore": cursor_id, "collection": capped.name})
    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg="getMore should succeed when maxTimeMS is omitted on awaitData tailable cursor",
        raw_res=True,
    )
