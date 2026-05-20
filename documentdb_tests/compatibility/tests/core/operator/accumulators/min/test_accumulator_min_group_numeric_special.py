"""Tests for $min accumulator — NaN, infinity, boundaries, Decimal128 ($group)."""

from __future__ import annotations

import math
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)


def _group_min(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline for $min."""
    return [{"$group": {"_id": None, "result": {"$min": accumulator}}}]


def _run_accumulator(collection, test_case: AccumulatorTestCase):
    """Insert docs and run the pipeline."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )


# ---------------------------------------------------------------------------
# Property [NaN Handling]: NaN compares as less than all other numeric values.
# For $min, NaN wins over all other numbers.
# ---------------------------------------------------------------------------
MIN_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_sole_float",
        docs=[{"v": FLOAT_NAN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should return float NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_sole_decimal",
        docs=[{"v": DECIMAL128_NAN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_NAN}],
        msg="$min should return Decimal128 NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_decimal_negative",
        docs=[{"v": Decimal128("-NaN")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("-NaN")}],
        msg="$min should preserve -NaN for Decimal128",
    ),
    AccumulatorTestCase(
        "nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 100}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over positive number (NaN < all numerics)",
    ),
    AccumulatorTestCase(
        "nan_vs_negative",
        docs=[{"v": FLOAT_NAN}, {"v": -100}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over negative number",
    ),
    AccumulatorTestCase(
        "nan_vs_neg_infinity",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over -Infinity (NaN < -Infinity)",
    ),
    AccumulatorTestCase(
        "nan_as_only_nonnull",
        docs=[{"v": FLOAT_NAN}, {"v": None}, {"x": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should return NaN when it is the only non-null value",
    ),
    AccumulatorTestCase(
        "nan_three_docs",
        docs=[{"v": FLOAT_NAN}, {"v": 5}, {"v": 10}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over multiple positive values",
    ),
]


# ---------------------------------------------------------------------------
# Property [Infinity Handling]: -Infinity < all finite values < +Infinity.
# NaN < -Infinity. For $min, -Infinity wins over finite values.
# ---------------------------------------------------------------------------
MIN_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "inf_vs_int32",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT32_MIN}],
        msg="$min should pick INT32_MIN over +Infinity",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_int32",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over INT32_MIN",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_int64",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over INT64_MIN",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_double",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_decimal",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick float -Infinity over DECIMAL128_MIN",
    ),
    AccumulatorTestCase(
        "decimal_neg_inf_vs_double_min",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_NEGATIVE_INFINITY}],
        msg="$min should pick Decimal128 -Infinity over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "inf_vs_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over +Infinity",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_neg_inf",
        docs=[{"v": Decimal128("Infinity")}, {"v": Decimal128("-Infinity")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("-Infinity")}],
        msg="$min should pick Decimal128 -Infinity over Decimal128 +Infinity",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_string",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": "hello"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity (Number) over String",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_nan",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": FLOAT_NAN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over -Infinity (NaN < -Infinity)",
    ),
]


# ---------------------------------------------------------------------------
# Property [Numeric Boundary Values]: boundary values across all numeric types
# are compared correctly. $min picks the numerically smallest value.
# ---------------------------------------------------------------------------
MIN_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max_vs_min",
        docs=[{"v": INT32_MAX}, {"v": INT32_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT32_MIN}],
        msg="$min should pick INT32_MIN over INT32_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_vs_min",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT64_MIN}],
        msg="$min should pick INT64_MIN over INT64_MAX",
    ),
    AccumulatorTestCase(
        "boundary_double_max_vs_min",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_MIN}],
        msg="$min should pick DOUBLE_MIN over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "boundary_decimal_max_vs_min",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MIN}],
        msg="$min should pick DECIMAL128_MIN over DECIMAL128_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_vs_int64_min",
        docs=[{"v": INT32_MIN}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT64_MIN}],
        msg="$min should pick INT64_MIN over INT32_MIN",
    ),
    AccumulatorTestCase(
        "boundary_double_min_vs_int64_min",
        docs=[{"v": DOUBLE_MIN}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_MIN}],
        msg="$min should pick DOUBLE_MIN over INT64_MIN (DOUBLE_MIN is more negative)",
    ),
    AccumulatorTestCase(
        "boundary_decimal_min_vs_double_min",
        docs=[{"v": DECIMAL128_MIN}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MIN}],
        msg="$min should pick DECIMAL128_MIN over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "boundary_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": 0.0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 0.0}],
        msg="$min should pick 0.0 over positive subnormal",
    ),
    AccumulatorTestCase(
        "boundary_neg_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, {"v": 0.0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        msg="$min should pick negative subnormal over 0.0",
    ),
    AccumulatorTestCase(
        "boundary_near_max",
        docs=[{"v": DOUBLE_NEAR_MAX}, {"v": DOUBLE_MAX}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_NEAR_MAX}],
        msg="$min should pick DOUBLE_NEAR_MAX over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int32_adjacent",
        docs=[{"v": INT32_MIN}, {"v": INT32_MIN + 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT32_MIN}],
        msg="$min should pick INT32_MIN over INT32_MIN+1",
    ),
    AccumulatorTestCase(
        "boundary_int64_adjacent",
        docs=[{"v": INT64_MIN}, {"v": Int64(int(INT64_MIN) + 1)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT64_MIN}],
        msg="$min should pick INT64_MIN over INT64_MIN+1",
    ),
]


# ---------------------------------------------------------------------------
# Property [Negative Zero]: negative zero and positive zero are numerically equal.
# Tie-breaking by document order differs by stage. These tests use $group (last wins).
# ---------------------------------------------------------------------------
MIN_NEGATIVE_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_vs_negative",
        docs=[{"v": -0.0}, {"v": -1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": -1}],
        msg="$min should pick -1 over -0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_vs_negative",
        docs=[{"v": Decimal128("-0")}, {"v": -1.0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": -1.0}],
        msg="$min should pick -1.0 over Decimal128('-0')",
    ),
]


# ---------------------------------------------------------------------------
# Property [Decimal128 Precision]: Decimal128 precision boundaries are handled correctly.
# ---------------------------------------------------------------------------
MIN_DECIMAL_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_high_precision",
        docs=[
            {"v": Decimal128("1.234567890123456789012345678901234")},
            {"v": Decimal128("1.234567890123456789012345678901235")},
        ],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("1.234567890123456789012345678901234")}],
        msg="$min should compare 34-digit Decimal128 values correctly",
    ),
    AccumulatorTestCase(
        "decimal_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_MAX}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_LARGE_EXPONENT}],
        msg="$min should pick Decimal128 with smaller large exponent",
    ),
    AccumulatorTestCase(
        "decimal_min_positive",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_ZERO}],
        msg="$min should pick zero over min positive Decimal128",
    ),
    AccumulatorTestCase(
        "decimal_max_negative",
        docs=[{"v": DECIMAL128_MAX_NEGATIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MAX_NEGATIVE}],
        msg="$min should pick max negative Decimal128 over zero",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_max",
        docs=[{"v": Decimal128("Infinity")}, {"v": DECIMAL128_MAX}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MAX}],
        msg="$min should pick DECIMAL128_MAX over Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "decimal_neg_inf_vs_min",
        docs=[{"v": Decimal128("-Infinity")}, {"v": DECIMAL128_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("-Infinity")}],
        msg="$min should pick Decimal128 -Infinity over DECIMAL128_MIN",
    ),
    AccumulatorTestCase(
        "decimal_nan_vs_finite",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_NAN}],
        msg="$min should pick Decimal128 NaN over finite Decimal128 (NaN < all)",
    ),
]


# ---------------------------------------------------------------------------
# Combined success tests
# ---------------------------------------------------------------------------
MIN_GROUP_NUMERIC_SPECIAL_SUCCESS_TESTS = (
    MIN_NAN_TESTS
    + MIN_INFINITY_TESTS
    + MIN_BOUNDARY_TESTS
    + MIN_NEGATIVE_ZERO_TESTS
    + MIN_DECIMAL_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_NUMERIC_SPECIAL_SUCCESS_TESTS))
def test_accumulator_min_group_numeric_special(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator NaN, infinity, boundaries, and Decimal128 precision with $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)
