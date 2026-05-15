"""
Tests for $avg accumulator data type handling in $group context.

Covers type promotion rules, NaN/Infinity propagation, null/missing handling,
and non-numeric type ignoring when accumulating across documents.
"""

from __future__ import annotations

import math

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Type Promotion]: $avg returns double for integer and double inputs,
# and Decimal128 when any input is Decimal128.
AVG_TYPE_PROMOTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "all_int32",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="int32 avg should return double",
    ),
    AccumulatorTestCase(
        "all_int64",
        docs=[
            {"_id": 0, "v": Int64(10)},
            {"_id": 1, "v": Int64(20)},
            {"_id": 2, "v": Int64(30)},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="int64 avg should return double",
    ),
    AccumulatorTestCase(
        "all_double",
        docs=[{"_id": 0, "v": 10.0}, {"_id": 1, "v": 20.0}, {"_id": 2, "v": 30.0}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="double avg should return double",
    ),
    AccumulatorTestCase(
        "all_decimal128",
        docs=[
            {"_id": 0, "v": Decimal128("10")},
            {"_id": 1, "v": Decimal128("20")},
            {"_id": 2, "v": Decimal128("30")},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("20")}],
        msg="decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "int32_and_int64",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": Int64(20)}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 15.0}],
        msg="int32+int64 avg should return double",
    ),
    AccumulatorTestCase(
        "int32_and_double",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20.0}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 15.0}],
        msg="int32+double avg should return double",
    ),
    AccumulatorTestCase(
        "int32_and_decimal128",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": Decimal128("20")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("15")}],
        msg="int32+decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "int64_and_decimal128",
        docs=[{"_id": 0, "v": Int64(10)}, {"_id": 1, "v": Decimal128("20")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("15")}],
        msg="int64+decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "double_and_decimal128",
        docs=[{"_id": 0, "v": 10.0}, {"_id": 1, "v": Decimal128("20")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("15")}],
        msg="double+decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "all_four_types",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": Int64(20)},
            {"_id": 2, "v": 30.0},
            {"_id": 3, "v": Decimal128("40")},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("25")}],
        msg="all four numeric types avg should return decimal128",
    ),
    AccumulatorTestCase(
        "fractional_result_from_int32",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 1.5}],
        msg="int32 avg producing fraction should return double",
    ),
]

# Property [NaN Propagation]: NaN is numeric and propagates to the result;
# NaN dominates Infinity and cross-type NaN promotes to Decimal128.
AVG_NAN_PROPAGATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_propagates",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": float("nan")}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="NaN in group should propagate to result",
    ),
    AccumulatorTestCase(
        "all_nan",
        docs=[{"_id": 0, "v": float("nan")}, {"_id": 1, "v": float("nan")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="All NaN in group should return NaN",
    ),
    AccumulatorTestCase(
        "decimal128_nan",
        docs=[
            {"_id": 0, "v": Decimal128("10")},
            {"_id": 1, "v": DECIMAL128_NAN},
            {"_id": 2, "v": Decimal128("30")},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_NAN}],
        msg="Decimal128 NaN in group should propagate",
    ),
    AccumulatorTestCase(
        "nan_dominates_infinity",
        docs=[{"_id": 0, "v": float("nan")}, {"_id": 1, "v": FLOAT_INFINITY}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="NaN should dominate Infinity in group",
    ),
    AccumulatorTestCase(
        "cross_type_nan",
        docs=[{"_id": 0, "v": float("nan")}, {"_id": 1, "v": Decimal128("5")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_NAN}],
        msg="double NaN + Decimal128 should return Decimal128 NaN",
    ),
]

# Property [Infinity]: Infinity dominates finite values, and
# Infinity + -Infinity cancels to NaN.
AVG_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "infinity",
        docs=[{"_id": 0, "v": FLOAT_INFINITY}, {"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": FLOAT_INFINITY}],
        msg="Infinity in group should propagate",
    ),
    AccumulatorTestCase(
        "negative_infinity",
        docs=[{"_id": 0, "v": FLOAT_NEGATIVE_INFINITY}, {"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": FLOAT_NEGATIVE_INFINITY}],
        msg="-Infinity in group should propagate",
    ),
    AccumulatorTestCase(
        "inf_neg_inf_cancel",
        docs=[{"_id": 0, "v": FLOAT_INFINITY}, {"_id": 1, "v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="Infinity + -Infinity in group should return NaN",
    ),
    AccumulatorTestCase(
        "decimal128_infinity",
        docs=[{"_id": 0, "v": DECIMAL128_INFINITY}, {"_id": 1, "v": Decimal128("10")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_INFINITY}],
        msg="Decimal128 Infinity in group should propagate",
    ),
    AccumulatorTestCase(
        "decimal128_inf_neg_inf_cancel",
        docs=[
            {"_id": 0, "v": DECIMAL128_INFINITY},
            {"_id": 1, "v": DECIMAL128_NEGATIVE_INFINITY},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_NAN}],
        msg="Decimal128 Inf + -Inf in group should return Decimal128 NaN",
    ),
]

# Property [Null and Missing]: null values and missing fields are excluded
# from both the sum and count, producing null when no numeric values remain.
AVG_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "all_null",
        docs=[{"_id": 0, "v": None}, {"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="All null in group should return null",
    ),
    AccumulatorTestCase(
        "some_null",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": None}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="Null docs should be ignored, avg of 10 and 30 is 20",
    ),
    AccumulatorTestCase(
        "all_missing",
        docs=[{"_id": 0, "other": 0}, {"_id": 1, "other": 1}, {"_id": 2, "other": 2}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="All missing fields should return null",
    ),
    AccumulatorTestCase(
        "some_missing",
        docs=[{"_id": 0, "v": 10}, {"_id": 1}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="Missing field docs should be ignored",
    ),
    AccumulatorTestCase(
        "mix_null_missing_numeric",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": 30},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="Only numeric values should contribute to average",
    ),
]

# Property [Non-Numeric Types Ignored]: non-numeric BSON types are silently
# ignored and excluded from both sum and count.
AVG_NON_NUMERIC_IGNORED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "ignores_strings",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": "hello"}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="String values should be ignored in group avg",
    ),
    AccumulatorTestCase(
        "ignores_booleans",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": True},
            {"_id": 2, "v": False},
            {"_id": 3, "v": 30},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="Boolean values should be ignored in group avg",
    ),
    AccumulatorTestCase(
        "ignores_arrays",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": [1, 2, 3]}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="Array values should be ignored in group avg",
    ),
    AccumulatorTestCase(
        "ignores_objects",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": {"nested": 99}}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="Object values should be ignored in group avg",
    ),
    AccumulatorTestCase(
        "all_non_numeric",
        docs=[
            {"_id": 0, "v": "a"},
            {"_id": 1, "v": True},
            {"_id": 2, "v": [1]},
            {"_id": 3, "v": {"x": 1}},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="All non-numeric values should return null",
    ),
    AccumulatorTestCase(
        "boolean_not_numeric",
        docs=[{"_id": 0, "v": False}, {"_id": 1, "v": True}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="Booleans should not be treated as 0/1 in avg",
    ),
]

# Property [Negative Zero]: $avg normalizes negative zero to positive zero
# for both double and Decimal128.
AVG_NEGATIVE_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negative_zero_double",
        docs=[
            {"_id": 0, "v": DOUBLE_NEGATIVE_ZERO},
            {"_id": 1, "v": DOUBLE_NEGATIVE_ZERO},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DOUBLE_ZERO}],
        msg="Double -0.0 avg should normalize to 0.0",
    ),
    AccumulatorTestCase(
        "negative_zero_decimal128",
        docs=[
            {"_id": 0, "v": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 1, "v": DECIMAL128_NEGATIVE_ZERO},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_ZERO}],
        msg="Decimal128 -0 avg should normalize to 0",
    ),
]

AVG_GROUP_TYPE_TESTS: list[AccumulatorTestCase] = (
    AVG_TYPE_PROMOTION_TESTS
    + AVG_NAN_PROPAGATION_TESTS
    + AVG_INFINITY_TESTS
    + AVG_NULL_MISSING_TESTS
    + AVG_NON_NUMERIC_IGNORED_TESTS
    + AVG_NEGATIVE_ZERO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_GROUP_TYPE_TESTS))
def test_avg_group_types(collection, test_case: AccumulatorTestCase):
    """Test $avg data type handling in $group context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
