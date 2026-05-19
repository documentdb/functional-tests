"""Tests for $sum accumulator: type promotion, overflow, and cross-type interactions."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Return Type and Type Promotion]: the result type is the widest
# numeric type present in the group following int32 < Int64 < double < Decimal128,
# with no demotion.
SUM_TYPE_PROMOTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_single_int32",
        docs=[{"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 5, "type": "int"},
        msg="$sum should preserve int32 type for a single int32 value",
    ),
    AccumulatorTestCase(
        "type_single_int64",
        docs=[{"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(5), "type": "long"},
        msg="$sum should preserve Int64 type for a single Int64 value",
    ),
    AccumulatorTestCase(
        "type_single_double",
        docs=[{"v": 5.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 5.5, "type": "double"},
        msg="$sum should preserve double type for a single double value",
    ),
    AccumulatorTestCase(
        "type_single_decimal128",
        docs=[{"v": Decimal128("5.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("5.5"), "type": "decimal"},
        msg="$sum should preserve Decimal128 type for a single Decimal128 value",
    ),
    AccumulatorTestCase(
        "type_int32_int64_promotes",
        docs=[{"v": 5}, {"v": Int64(10)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(15), "type": "long"},
        msg="$sum should promote int32 + Int64 to Int64",
    ),
    AccumulatorTestCase(
        "type_int32_double_promotes",
        docs=[{"v": 5}, {"v": 2.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 7.5, "type": "double"},
        msg="$sum should promote int32 + double to double",
    ),
    AccumulatorTestCase(
        "type_int64_double_promotes",
        docs=[{"v": Int64(5)}, {"v": 2.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 7.5, "type": "double"},
        msg="$sum should promote Int64 + double to double",
    ),
    AccumulatorTestCase(
        "type_int32_decimal128_promotes",
        docs=[{"v": 5}, {"v": DECIMAL128_TWO_AND_HALF}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("7.5"), "type": "decimal"},
        msg="$sum should promote int32 + Decimal128 to Decimal128",
    ),
    AccumulatorTestCase(
        "type_int64_decimal128_promotes",
        docs=[{"v": Int64(5)}, {"v": Decimal128("3")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("8"), "type": "decimal"},
        msg="$sum should promote Int64 + Decimal128 to Decimal128",
    ),
    AccumulatorTestCase(
        "type_double_decimal128_promotes",
        docs=[{"v": 2.5}, {"v": Decimal128("3.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("6.0"), "type": "decimal"},
        msg="$sum should promote double + Decimal128 to Decimal128",
    ),
    AccumulatorTestCase(
        "type_no_demotion_int64_fits_int32",
        docs=[{"v": Int64(1)}, {"v": Int64(2)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(3), "type": "long"},
        msg="$sum should not demote Int64 to int32 even when result fits int32",
    ),
    AccumulatorTestCase(
        "type_all_non_numeric_is_int32",
        docs=[{"v": "abc"}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 0, "type": "int"},
        msg="$sum should return int32 zero when all values are non-numeric",
    ),
]

# Property [Overflow Behavior]: double and Decimal128 overflow produces
# infinity without type promotion.
SUM_OVERFLOW_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "overflow_double_positive",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": FLOAT_INFINITY, "type": "double"},
        msg="$sum should produce positive infinity on double overflow",
    ),
    AccumulatorTestCase(
        "overflow_double_negative",
        docs=[{"v": DOUBLE_MIN}, {"v": DOUBLE_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": FLOAT_NEGATIVE_INFINITY, "type": "double"},
        msg="$sum should produce negative infinity on double overflow",
    ),
    AccumulatorTestCase(
        "overflow_decimal128_positive",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should produce Decimal128 Infinity on positive overflow",
    ),
    AccumulatorTestCase(
        "overflow_decimal128_negative",
        docs=[{"v": DECIMAL128_MIN}, {"v": DECIMAL128_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NEGATIVE_INFINITY, "type": "decimal"},
        msg="$sum should produce Decimal128 -Infinity on negative overflow",
    ),
]

# Property [Overflow Recovery]: if intermediate values overflow but the final
# sum fits the original type, the result is returned in the original type.
# Double and Decimal128 overflow does not recover once infinity is reached.
SUM_OVERFLOW_RECOVERY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "recovery_int32_positive",
        docs=[{"v": INT32_MAX}, {"v": 1000}, {"v": -1000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should recover int32 when intermediate overflows but final fits int32",
    ),
    AccumulatorTestCase(
        "recovery_int32_negative",
        docs=[{"v": INT32_MIN}, {"v": -1000}, {"v": 1000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should recover int32 when intermediate underflows but final fits int32",
    ),
    AccumulatorTestCase(
        "recovery_int64_positive",
        docs=[{"v": INT64_MAX}, {"v": Int64(100)}, {"v": Int64(-100)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should recover Int64 when intermediate overflows but final fits Int64",
    ),
    AccumulatorTestCase(
        "recovery_int64_negative",
        docs=[{"v": INT64_MIN}, {"v": Int64(-1000)}, {"v": Int64(1000)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should recover Int64 when intermediate underflows but final fits Int64",
    ),
    AccumulatorTestCase(
        "recovery_double_no_recover",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": FLOAT_INFINITY, "type": "double"},
        msg="$sum should not recover double once intermediate reaches infinity",
    ),
    AccumulatorTestCase(
        "recovery_decimal128_no_recover",
        docs=[
            {"v": DECIMAL128_MAX},
            {"v": DECIMAL128_MAX},
            {"v": DECIMAL128_MIN},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should not recover Decimal128 once intermediate reaches Infinity",
    ),
]

# Property [Decimal128 Presence Changes Overflow Path]: when Int64 values
# overflow and a Decimal128 value is present in the group, the result is
# Decimal128 with exact precision instead of promoting to double.
SUM_DECIMAL128_OVERFLOW_PATH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal128_path_int64_overflow_with_decimal_zero",
        docs=[{"v": INT64_MAX}, {"v": Int64(1)}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce exact Decimal128 when Int64 overflows with Decimal128(0) present",
    ),
    AccumulatorTestCase(
        "decimal128_path_decimal_first",
        docs=[{"v": DECIMAL128_ZERO}, {"v": INT64_MAX}, {"v": Int64(1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce Decimal128 regardless of Decimal128 position in group",
    ),
    AccumulatorTestCase(
        "decimal128_path_double_does_not_redirect",
        docs=[{"v": INT64_MAX}, {"v": Int64(1)}, {"v": DOUBLE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should not redirect Int64 overflow to Decimal128 when only double is present",
    ),
    AccumulatorTestCase(
        "decimal128_path_both_double_and_decimal128",
        docs=[
            {"v": INT64_MAX},
            {"v": Int64(1)},
            {"v": DOUBLE_ZERO},
            {"v": DECIMAL128_ZERO},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce Decimal128 when both double and Decimal128 present with overflow",
    ),
]

# Property [Cross-Type NaN/Infinity Interactions]: when double NaN or infinity
# is mixed with Decimal128 values, the result is promoted to Decimal128 with
# NaN or Infinity propagating in the Decimal128 domain.
SUM_CROSS_TYPE_NAN_INF_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "cross_type_double_nan_plus_decimal128",
        docs=[{"v": FLOAT_NAN}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should promote double NaN + Decimal128 to Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "cross_type_decimal128_nan_plus_double",
        docs=[{"v": DECIMAL128_NAN}, {"v": 5.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should promote Decimal128 NaN + double to Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "cross_type_double_inf_plus_decimal128",
        docs=[{"v": FLOAT_INFINITY}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should promote double inf + Decimal128 to Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "cross_type_double_neg_inf_plus_decimal128_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should produce Decimal128 NaN for double -inf + Decimal128 Infinity",
    ),
]

SUM_TYPE_TESTS = (
    SUM_TYPE_PROMOTION_TESTS
    + SUM_OVERFLOW_TESTS
    + SUM_OVERFLOW_RECOVERY_TESTS
    + SUM_DECIMAL128_OVERFLOW_PATH_TESTS
    + SUM_CROSS_TYPE_NAN_INF_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_TYPE_TESTS))
def test_sum_type_promotion(collection, test_case: AccumulatorTestCase):
    """Test $sum return type promotion, overflow, and cross-type interactions."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(
        result,
        [test_case.expected],
        msg=test_case.msg,
    )
