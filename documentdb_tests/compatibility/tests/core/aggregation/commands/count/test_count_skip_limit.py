"""Tests for count command skip and limit behavior."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_NAN,
    INT64_MAX,
)

# Property [Skip Behavior]: skip reduces the counted result by the specified
# number of documents, with no effect when zero or absent.
COUNT_SKIP_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "skip_zero",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "skip": 0},
        expected={"n": 5, "ok": 1.0},
        msg="count with skip=0 should return full count",
    ),
    CommandTestCase(
        "skip_partial",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 3},
        expected={"n": 7, "ok": 1.0},
        msg="count with skip=3 and 10 docs should return 7",
    ),
    CommandTestCase(
        "skip_equals_count",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "skip": 5},
        expected={"n": 0, "ok": 1.0},
        msg="count with skip equal to document count should return 0",
    ),
    CommandTestCase(
        "skip_exceeds_count",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "skip": 10},
        expected={"n": 0, "ok": 1.0},
        msg="count with skip exceeding document count should return 0",
    ),
    CommandTestCase(
        "skip_int64_max",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "skip": INT64_MAX},
        expected={"n": 0, "ok": 1.0},
        msg="count with skip=Int64(max) should skip all documents",
    ),
]

# Property [Skip and Limit Interaction]: skip and limit combine to constrain
# the counted result.
COUNT_SKIP_LIMIT_INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "skip_limit_basic",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 3, "limit": 5},
        expected={"n": 5, "ok": 1.0},
        msg="count with skip=3, limit=5, 10 docs should return min(5, max(0, 10-3)) = 5",
    ),
    CommandTestCase(
        "skip_limit_limit_caps",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 8, "limit": 5},
        expected={"n": 2, "ok": 1.0},
        msg="count with skip=8, limit=5, 10 docs should return min(5, max(0, 10-8)) = 2",
    ),
    CommandTestCase(
        "skip_limit_zero_means_no_limit",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 3, "limit": 0},
        expected={"n": 7, "ok": 1.0},
        msg="count with limit=0 should mean no limit: max(0, 10-3) = 7",
    ),
    CommandTestCase(
        "skip_limit_skip_exceeds_matching",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 15, "limit": 5},
        expected={"n": 0, "ok": 1.0},
        msg="count should return 0 when skip exceeds matching document count",
    ),
    CommandTestCase(
        "skip_limit_skip_exceeds_no_limit",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 15, "limit": 0},
        expected={"n": 0, "ok": 1.0},
        msg="count should return 0 when skip exceeds matching count even with no limit",
    ),
    CommandTestCase(
        "skip_limit_negative_limit",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 2, "limit": -3},
        expected={"n": 3, "ok": 1.0},
        msg="count with negative limit should use abs value: min(3, max(0, 10-2)) = 3",
    ),
    CommandTestCase(
        "skip_limit_with_query",
        docs=[{"_id": i, "x": i} for i in range(10)],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": {"$gt": 4}},
            "skip": 1,
            "limit": 2,
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with query (5 match), skip=1, limit=2 should return min(2, max(0, 5-1)) = 2",
    ),
]

# Property [Limit Behavior]: limit caps the count result with special handling
# of zero and negative values.
COUNT_LIMIT_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "limit_zero_int",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": 0},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=0 should return full count (no limit)",
    ),
    CommandTestCase(
        "limit_zero_double",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": DOUBLE_ZERO},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=0.0 should return full count (no limit)",
    ),
    CommandTestCase(
        "limit_negative_three",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": -3},
        expected={"n": 3, "ok": 1.0},
        msg="count with limit=-3 should be treated as abs(3)",
    ),
    CommandTestCase(
        "limit_negative_exceeds_count",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": -10},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=-10 and 5 docs should return 5 (abs exceeds count)",
    ),
    CommandTestCase(
        "limit_neg_zero_double",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": DOUBLE_NEGATIVE_ZERO},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=-0.0 should be treated as 0 (no limit)",
    ),
    CommandTestCase(
        "limit_neg_zero_decimal",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "limit": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"n": 5, "ok": 1.0},
        msg='count with limit=Decimal128("-0") should be treated as 0 (no limit)',
    ),
    CommandTestCase(
        "limit_neg_zero_decimal_fractional",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "limit": Decimal128("-0.0"),
        },
        expected={"n": 5, "ok": 1.0},
        msg='count with limit=Decimal128("-0.0") should be treated as 0 (no limit)',
    ),
    CommandTestCase(
        "limit_negative_int64",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": Int64(-3)},
        expected={"n": 3, "ok": 1.0},
        msg="count with limit=Int64(-3) should be treated as abs(3)",
    ),
    CommandTestCase(
        "limit_negative_decimal128",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": Decimal128("-3")},
        expected={"n": 3, "ok": 1.0},
        msg='count with limit=Decimal128("-3") should be treated as abs(3)',
    ),
    CommandTestCase(
        "limit_int64_max",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": INT64_MAX},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=Int64(max) should effectively mean no limit",
    ),
]

# Property [Skip Coercion]: non-integer numeric skip values are coerced to
# integers before being applied.
COUNT_SKIP_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "skip_coerce_double_1_5",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 1.5},
        expected={"n": 9, "ok": 1.0},
        msg="count skip=1.5 (double) should truncate toward zero to 1",
    ),
    CommandTestCase(
        "skip_coerce_double_2_5",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 2.5},
        expected={"n": 8, "ok": 1.0},
        msg="count skip=2.5 (double) should truncate toward zero to 2",
    ),
    CommandTestCase(
        "skip_coerce_double_3_5",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 3.5},
        expected={"n": 7, "ok": 1.0},
        msg="count skip=3.5 (double) should truncate toward zero to 3",
    ),
    CommandTestCase(
        "skip_coerce_decimal128_1_5",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_ONE_AND_HALF},
        expected={"n": 8, "ok": 1.0},
        msg='count skip=Decimal128("1.5") should use banker\'s rounding to 2',
    ),
    CommandTestCase(
        "skip_coerce_decimal128_2_5",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_TWO_AND_HALF},
        expected={"n": 8, "ok": 1.0},
        msg='count skip=Decimal128("2.5") should use banker\'s rounding to 2',
    ),
    CommandTestCase(
        "skip_coerce_decimal128_3_5",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": Decimal128("3.5")},
        expected={"n": 6, "ok": 1.0},
        msg='count skip=Decimal128("3.5") should use banker\'s rounding to 4',
    ),
    CommandTestCase(
        "skip_coerce_decimal128_4_5",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": Decimal128("4.5")},
        expected={"n": 6, "ok": 1.0},
        msg='count skip=Decimal128("4.5") should use banker\'s rounding to 4',
    ),
    CommandTestCase(
        "skip_coerce_double_nan",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": FLOAT_NAN},
        expected={"n": 10, "ok": 1.0},
        msg="count skip=NaN (double) should be treated as 0",
    ),
    CommandTestCase(
        "skip_coerce_double_neg_nan",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": FLOAT_NEGATIVE_NAN},
        expected={"n": 10, "ok": 1.0},
        msg="count skip=-NaN (double) should be treated as 0",
    ),
    CommandTestCase(
        "skip_coerce_decimal128_nan",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_NAN},
        expected={"n": 10, "ok": 1.0},
        msg="count skip=NaN (Decimal128) should be treated as 0",
    ),
    CommandTestCase(
        "skip_coerce_decimal128_neg_nan",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_NEGATIVE_NAN},
        expected={"n": 10, "ok": 1.0},
        msg="count skip=-NaN (Decimal128) should be treated as 0",
    ),
    CommandTestCase(
        "skip_coerce_double_pos_inf",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": FLOAT_INFINITY},
        expected={"n": 0, "ok": 1.0},
        msg="count skip=+Infinity (double) should skip all documents",
    ),
    CommandTestCase(
        "skip_coerce_decimal128_pos_inf",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_INFINITY},
        expected={"n": 0, "ok": 1.0},
        msg="count skip=+Infinity (Decimal128) should skip all documents",
    ),
    CommandTestCase(
        "skip_coerce_double_neg_zero",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DOUBLE_NEGATIVE_ZERO},
        expected={"n": 10, "ok": 1.0},
        msg="count skip=-0.0 (double) should be treated as 0",
    ),
    CommandTestCase(
        "skip_coerce_decimal128_neg_zero",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_NEGATIVE_ZERO},
        expected={"n": 10, "ok": 1.0},
        msg='count skip=Decimal128("-0") should be treated as 0',
    ),
    CommandTestCase(
        "skip_coerce_subnormal_double",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DOUBLE_MIN_SUBNORMAL},
        expected={"n": 10, "ok": 1.0},
        msg="count skip=subnormal double should truncate to 0",
    ),
    CommandTestCase(
        "skip_coerce_decimal128_tiny_exponent",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_MIN_POSITIVE},
        expected={"n": 10, "ok": 1.0},
        msg='count skip=Decimal128("1E-6176") should round to 0',
    ),
    CommandTestCase(
        "skip_coerce_decimal128_huge_exponent",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_LARGE_EXPONENT},
        expected={"n": 0, "ok": 1.0},
        msg='count skip=Decimal128("1E+6144") should skip all documents',
    ),
]

COUNT_SKIP_LIMIT_TESTS: list[CommandTestCase] = (
    COUNT_SKIP_BEHAVIOR_TESTS
    + COUNT_SKIP_LIMIT_INTERACTION_TESTS
    + COUNT_LIMIT_BEHAVIOR_TESTS
    + COUNT_SKIP_COERCION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_SKIP_LIMIT_TESTS))
def test_count_skip_limit(database_client, collection, test):
    """Test count command skip and limit behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
