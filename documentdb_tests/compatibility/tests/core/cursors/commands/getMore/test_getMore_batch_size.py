"""Tests for getMore batchSize numeric coercion and limits."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_MAX,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT64_MAX,
    INT64_ZERO,
)

# Number of documents inserted before each coercion test. The originating find
# uses find_batch_size, so DOC_COUNT minus find_batch_size documents remain for
# the getMore under test.
DOC_COUNT = 10

# Property [Integer Pass-Through]: integer batchSize values are used as the
# batch size directly without coercion.
GETMORE_BATCH_SIZE_INTEGER_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "integer_int32",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": 4,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(4)}},
        msg="getMore should use int32 batchSize as-is",
    ),
    CursorCommandTestCase(
        "integer_int64",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": Int64(4),
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(4)}},
        msg="getMore should use int64 batchSize as-is",
    ),
]

# Property [batchSize Numeric Coercion]: fractional batchSize values that round
# to a positive integer use that integer as the batch size, with rounding that
# depends on the numeric type (doubles truncate toward zero, Decimal128 uses
# banker's rounding).
GETMORE_BATCH_SIZE_COERCION_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "coerce_double_1_5",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": 1.5,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(1)}},
        msg="getMore should truncate double 1.5 to 1",
    ),
    CursorCommandTestCase(
        "coerce_decimal_1_5",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_ONE_AND_HALF,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(2)}},
        msg="getMore should round Decimal128 1.5 to 2 (banker's rounding, even)",
    ),
    CursorCommandTestCase(
        "coerce_decimal_2_5",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_TWO_AND_HALF,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(2)}},
        msg="getMore should round Decimal128 2.5 to 2 (banker's rounding, even)",
    ),
    CursorCommandTestCase(
        "coerce_decimal_trailing_zeros_1_0",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_TRAILING_ZERO,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(1)}},
        msg="getMore should round Decimal128 1.0 to 1 (trailing zeros ignored)",
    ),
    CursorCommandTestCase(
        "coerce_decimal_just_above_half",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_JUST_ABOVE_HALF,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(1)}},
        msg="getMore should round Decimal128 just above 0.5 to 1",
    ),
]

# Property [batchSize Effective Zero]: an omitted or null batchSize, literal 0,
# and any value that coerces to 0 (NaN of either sign, negative zero, subnormal,
# and fractional values that round to 0) return all remaining documents and
# close a non-tailable cursor (cursor.id 0).
GETMORE_BATCH_SIZE_EFFECTIVE_ZERO_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "zero_omitted",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {"getMore": ctx.cursors[0], "collection": ctx.collection},
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore without batchSize should return all remaining and close cursor",
    ),
    CursorCommandTestCase(
        "zero_null",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": None,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore batchSize=null should return all remaining and close cursor",
    ),
    CursorCommandTestCase(
        "zero_literal",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": 0,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore batchSize=0 should return all remaining and close non-tailable cursor",
    ),
    CursorCommandTestCase(
        "zero_double_0_5",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": 0.5,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should truncate double 0.5 to 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_double_neg_0_99999",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": -0.99999,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should truncate double -0.99999 to 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_decimal_0_5",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_HALF,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should round Decimal128 0.5 to 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_decimal_neg_0_5",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_NEGATIVE_HALF,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should round Decimal128 -0.5 to 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_decimal_just_below_half",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_JUST_BELOW_HALF,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should round Decimal128 just below 0.5 to 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_double_nan",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": FLOAT_NAN,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should treat double NaN as batchSize 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_decimal_nan",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_NAN,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should treat Decimal128 NaN as batchSize 0 (returns all and closes cursor)",
    ),
    # Negative NaN ignores the sign bit and behaves like NaN (coerces to 0).
    CursorCommandTestCase(
        "zero_double_neg_nan",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": FLOAT_NEGATIVE_NAN,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should treat double -NaN as batchSize 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_decimal_neg_nan",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_NEGATIVE_NAN,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should treat Decimal128 -NaN as batchSize 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_double_neg_zero",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should accept double -0.0 as batchSize 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_decimal_neg_zero",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should accept Decimal128 -0 as batchSize 0 (returns all and closes cursor)",
    ),
    CursorCommandTestCase(
        "zero_double_subnormal",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DOUBLE_MIN_SUBNORMAL,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2), "id": Eq(INT64_ZERO)}},
        msg="getMore should truncate subnormal double to 0 (returns all and closes cursor)",
    ),
]

# Property [batchSize Value Boundaries]: batchSize=1 is the minimum effective
# size, and large values up to and beyond each numeric type's maximum (including
# infinity) are accepted and return all remaining documents with no upper bound.
GETMORE_BATCH_SIZE_BOUNDARY_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "boundary_one",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": 1,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(1)}},
        msg="getMore batchSize=1 should return exactly 1 document",
    ),
    CursorCommandTestCase(
        "boundary_int32_max",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": INT32_MAX,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should accept int32 max as batchSize and return all remaining",
    ),
    CursorCommandTestCase(
        "boundary_int64_max",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": INT64_MAX,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should accept int64 max as batchSize and return all remaining",
    ),
    CursorCommandTestCase(
        "boundary_double_2_pow_53",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DOUBLE_MAX_SAFE_INTEGER,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should accept double 2^53 and return all remaining",
    ),
    CursorCommandTestCase(
        "boundary_double_max",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DOUBLE_MAX,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should accept double max as batchSize and return all remaining",
    ),
    CursorCommandTestCase(
        "boundary_decimal_beyond_int64_max",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_MAX_COEFFICIENT,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should accept Decimal128 beyond int64 max and return all remaining",
    ),
    CursorCommandTestCase(
        "boundary_decimal_max",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_MAX,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should accept Decimal128 max as batchSize and return all remaining",
    ),
    CursorCommandTestCase(
        "boundary_double_infinity",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": FLOAT_INFINITY,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should treat double Infinity as returning all remaining",
    ),
    CursorCommandTestCase(
        "boundary_decimal_infinity",
        cursor_count=1,
        find_batch_size=2,
        command=lambda ctx: {
            "getMore": ctx.cursors[0],
            "collection": ctx.collection,
            "batchSize": DECIMAL128_INFINITY,
        },
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(DOC_COUNT - 2)}},
        msg="getMore should treat Decimal128 Infinity as returning all remaining",
    ),
]

GETMORE_BATCH_SIZE_TESTS = (
    GETMORE_BATCH_SIZE_INTEGER_TESTS
    + GETMORE_BATCH_SIZE_COERCION_TESTS
    + GETMORE_BATCH_SIZE_EFFECTIVE_ZERO_TESTS
    + GETMORE_BATCH_SIZE_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_BATCH_SIZE_TESTS))
def test_getMore_batch_size_coercion(collection, test_case: CursorCommandTestCase):
    """Test getMore batchSize numeric coercion."""
    collection.insert_many([{"_id": i, "v": i} for i in range(DOC_COUNT)])
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


# Property [16 MiB Batch Limit]: the 16 MiB batch limit caps the number of
# documents returned when documents are large.
def test_getMore_16mib_batch_limit(collection):
    """Test getMore 16 MiB batch limit caps large documents."""
    # Each document is ~1.1 MB, so the 16 MiB batch limit allows exactly 15.
    big_val = "x" * 1_100_000
    docs = [{"_id": i, "data": big_val} for i in range(20)]
    collection.insert_many(docs)
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(15)}},
        msg="getMore should cap batch at 16 MiB worth of documents",
        raw_res=True,
    )


# Property [batchSize Below Size Limit]: batchSize caps the batch when it is
# smaller than what the 16 MiB size limit would allow.
def test_getMore_16mib_batch_size_wins(collection):
    """Test getMore batchSize wins when smaller than 16 MiB would allow."""
    big_val = "x" * 1_100_000
    docs = [{"_id": i, "data": big_val} for i in range(20)]
    collection.insert_many(docs)
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 3},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3)}},
        msg="getMore batchSize=3 should return exactly 3 documents despite 16 MiB allowing more",
        raw_res=True,
    )
