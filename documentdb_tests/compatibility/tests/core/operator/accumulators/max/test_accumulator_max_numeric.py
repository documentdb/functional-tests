"""Tests for $max accumulator numeric edge cases: NaN, infinity, boundaries, and precision."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
)

# ===========================================================================
# 1. NaN Handling
# ===========================================================================

# Property [NaN Behavior]: NaN compares as less than all other numeric values
# (including negative infinity) in BSON comparison order. As the sole value,
# NaN is returned. Decimal128 -NaN is preserved.
MAX_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_sole_float",
        docs=[{"v": FLOAT_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$max should return float NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_sole_decimal",
        docs=[{"v": DECIMAL128_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_NAN}],
        msg="$max should return Decimal128 NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_decimal_negative",
        docs=[{"v": DECIMAL128_NEGATIVE_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_NEGATIVE_NAN}],
        msg="$max should preserve Decimal128 -NaN as sole value",
    ),
    AccumulatorTestCase(
        "nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should pick positive number over float NaN",
    ),
    AccumulatorTestCase(
        "nan_vs_negative",
        docs=[{"v": FLOAT_NAN}, {"v": -1000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -1000}],
        msg="$max should pick negative number over float NaN (NaN < all numerics)",
    ),
    AccumulatorTestCase(
        "nan_vs_neg_infinity",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_NEGATIVE_INFINITY}],
        msg="$max should pick -Infinity over float NaN",
    ),
    AccumulatorTestCase(
        "nan_as_only_nonnull",
        docs=[{"v": None}, {"v": FLOAT_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$max should return NaN when it is the only non-null value",
    ),
    AccumulatorTestCase(
        "nan_three_docs",
        docs=[{"v": FLOAT_NAN}, {"v": 5}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10}],
        msg="$max should pick 10 over NaN and 5",
    ),
]


# ===========================================================================
# 2. Infinity Handling
# ===========================================================================

# Property [Infinity Comparison]: +Infinity > all finite values; -Infinity
# < all finite values but > NaN. String > Number in BSON order, so Infinity
# < any string.
MAX_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "inf_vs_int32",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over INT32_MAX",
    ),
    AccumulatorTestCase(
        "inf_vs_int64",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over INT64_MAX",
    ),
    AccumulatorTestCase(
        "inf_vs_double",
        docs=[{"v": FLOAT_INFINITY}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "inf_vs_decimal128",
        docs=[{"v": FLOAT_INFINITY}, {"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick float Infinity over DECIMAL128_MAX",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_double",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$max should pick Decimal128 Infinity over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_int32",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT32_MIN}],
        msg="$max should pick INT32_MIN over -Infinity",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_decimal",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MIN}],
        msg="$max should pick DECIMAL128_MIN over -Infinity",
    ),
    AccumulatorTestCase(
        "inf_vs_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over -Infinity",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_neg_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$max should pick Decimal128 Infinity over Decimal128 -Infinity",
    ),
    AccumulatorTestCase(
        "inf_vs_string",
        docs=[{"v": FLOAT_INFINITY}, {"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$max should pick string over Infinity (string > number in BSON order)",
    ),
]


# ===========================================================================
# 3. Numeric Boundary Values
# ===========================================================================

# Property [Numeric Boundaries]: boundary values across all numeric types
# are compared correctly.
MAX_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max_vs_min",
        docs=[{"v": INT32_MAX}, {"v": INT32_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT32_MAX}],
        msg="$max should pick INT32_MAX over INT32_MIN",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_vs_min",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT64_MAX}],
        msg="$max should pick INT64_MAX over INT64_MIN",
    ),
    AccumulatorTestCase(
        "boundary_double_max_vs_min",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MAX}],
        msg="$max should pick DOUBLE_MAX over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "boundary_decimal_max_vs_min",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MAX}],
        msg="$max should pick DECIMAL128_MAX over DECIMAL128_MIN",
    ),
    AccumulatorTestCase(
        "boundary_int32_max_vs_int64_max",
        docs=[{"v": INT32_MAX}, {"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT64_MAX}],
        msg="$max should pick INT64_MAX over INT32_MAX",
    ),
    AccumulatorTestCase(
        "boundary_double_max_vs_int64_max",
        docs=[{"v": DOUBLE_MAX}, {"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MAX}],
        msg="$max should pick DOUBLE_MAX over INT64_MAX",
    ),
    AccumulatorTestCase(
        "boundary_decimal_max_vs_double_max",
        docs=[{"v": DECIMAL128_MAX}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MAX}],
        msg="$max should pick DECIMAL128_MAX over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "boundary_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_SUBNORMAL}],
        msg="$max should pick smallest positive subnormal over zero",
    ),
    AccumulatorTestCase(
        "boundary_neg_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, {"v": DOUBLE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_ZERO}],
        msg="$max should pick zero over negative subnormal",
    ),
    AccumulatorTestCase(
        "boundary_near_max",
        docs=[{"v": DOUBLE_NEAR_MAX}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MAX}],
        msg="$max should pick DOUBLE_MAX over DOUBLE_NEAR_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int32_adjacent",
        docs=[{"v": INT32_MAX}, {"v": INT32_MAX_MINUS_1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT32_MAX}],
        msg="$max should pick INT32_MAX over INT32_MAX - 1",
    ),
    AccumulatorTestCase(
        "boundary_int64_adjacent",
        docs=[{"v": INT64_MAX}, {"v": INT64_MAX_MINUS_1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT64_MAX}],
        msg="$max should pick INT64_MAX over INT64_MAX - 1",
    ),
    AccumulatorTestCase(
        "boundary_safe_integer",
        docs=[{"v": DOUBLE_MAX_SAFE_INTEGER}, {"v": DOUBLE_PRECISION_LOSS}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(DOUBLE_PRECISION_LOSS)}],
        msg="$max should pick DOUBLE_PRECISION_LOSS over "
        "DOUBLE_MAX_SAFE_INTEGER at precision boundary",
    ),
]


# ===========================================================================
# 4. Negative Zero
# ===========================================================================

# Property [Negative Zero]: -0.0 and +0.0 are numerically equal; $max picks
# the larger of the two (which are equal), so the result depends on document
# order tie-breaking.
MAX_NEGZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_vs_positive",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 1}],
        msg="$max should pick positive number over double -0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_vs_positive",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": 1.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 1.0}],
        msg="$max should pick positive number over Decimal128 -0",
    ),
]


# ===========================================================================
# 5. Decimal128 Precision
# ===========================================================================

# Property [Decimal128 Precision]: Decimal128 precision boundaries are
# handled correctly.
MAX_DECIMAL_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_high_precision",
        docs=[
            {"v": Decimal128("1.234567890123456789012345678901234")},
            {"v": Decimal128("1.234567890123456789012345678901235")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("1.234567890123456789012345678901235")}],
        msg="$max should distinguish 34-digit Decimal128 values",
    ),
    AccumulatorTestCase(
        "decimal_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MAX}],
        msg="$max should pick DECIMAL128_MAX over DECIMAL128_LARGE_EXPONENT",
    ),
    AccumulatorTestCase(
        "decimal_min_positive",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MIN_POSITIVE}],
        msg="$max should pick DECIMAL128_MIN_POSITIVE over zero",
    ),
    AccumulatorTestCase(
        "decimal_max_negative",
        docs=[{"v": DECIMAL128_MAX_NEGATIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_ZERO}],
        msg="$max should pick zero over DECIMAL128_MAX_NEGATIVE",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_max",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$max should pick Decimal128 Infinity over DECIMAL128_MAX",
    ),
    AccumulatorTestCase(
        "decimal_neg_inf_vs_min",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MIN}],
        msg="$max should pick DECIMAL128_MIN over Decimal128 -Infinity",
    ),
    AccumulatorTestCase(
        "decimal_nan_vs_finite",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("5")}],
        msg="$max should pick finite Decimal128 over Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "decimal_small_exponent",
        docs=[{"v": DECIMAL128_SMALL_EXPONENT}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_SMALL_EXPONENT}],
        msg="$max should pick DECIMAL128_SMALL_EXPONENT over zero",
    ),
]


# ===========================================================================
# 6. Return Type Verification
# ===========================================================================

# Property [Return Type]: $max preserves the BSON type of the maximum value.
MAX_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_int32",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 30, "type": "int"}],
        msg="$max of int32 values should return type 'int'",
    ),
    AccumulatorTestCase(
        "return_type_int64",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Int64(300), "type": "long"}],
        msg="$max of int64 values should return type 'long'",
    ),
    AccumulatorTestCase(
        "return_type_double",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 3.5, "type": "double"}],
        msg="$max of double values should return type 'double'",
    ),
    AccumulatorTestCase(
        "return_type_decimal",
        docs=[{"v": Decimal128("1")}, {"v": Decimal128("3")}, {"v": Decimal128("2")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Decimal128("3"), "type": "decimal"}],
        msg="$max of Decimal128 values should return type 'decimal'",
    ),
    AccumulatorTestCase(
        "return_type_string",
        docs=[{"v": "a"}, {"v": "c"}, {"v": "b"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": "c", "type": "string"}],
        msg="$max of string values should return type 'string'",
    ),
    AccumulatorTestCase(
        "return_type_boolean",
        docs=[{"v": True}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": True, "type": "bool"}],
        msg="$max of boolean values should return type 'bool'",
    ),
    AccumulatorTestCase(
        "return_type_date",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": datetime(2023, 1, 1, tzinfo=timezone.utc), "type": "date"}],
        msg="$max of datetime values should return type 'date'",
    ),
    AccumulatorTestCase(
        "return_type_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": None, "type": "null"}],
        msg="$max of all null values should return type 'null'",
    ),
]


# ===========================================================================
# Combined success tests and test functions
# ===========================================================================

MAX_NUMERIC_SUCCESS_TESTS = (
    MAX_NAN_TESTS
    + MAX_INFINITY_TESTS
    + MAX_BOUNDARY_TESTS
    + MAX_NEGZERO_TESTS
    + MAX_DECIMAL_PRECISION_TESTS
    + MAX_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_NUMERIC_SUCCESS_TESTS))
def test_accumulator_max_numeric(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator numeric edge cases and return type preservation via $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
