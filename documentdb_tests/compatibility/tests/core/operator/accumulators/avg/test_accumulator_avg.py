"""Tests for $avg accumulator in $group context."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_MAX,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_NORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
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
    INT64_MIN_PLUS_1,
    INT64_ZERO,
)

# Property [Null and Missing Ignored]: null values, missing fields, and
# $$REMOVE are treated as non-numeric and excluded from both the sum and
# count, producing null when no numeric values remain.
AVG_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all_null",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when all values in the group are null",
    ),
    AccumulatorTestCase(
        "null_all_missing",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when all values reference missing fields",
    ),
    AccumulatorTestCase(
        "null_single_null",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when the only value is null",
    ),
    AccumulatorTestCase(
        "null_single_missing",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when the only value is a missing field",
    ),
    AccumulatorTestCase(
        "null_mixed_null_and_missing",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null when values are a mix of null and missing",
    ),
    AccumulatorTestCase(
        "null_with_numerics",
        docs=[{"v": None}, {"v": 10}, {"v": 20}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 15.0}],
        msg="$avg should exclude null from both sum and count",
    ),
    AccumulatorTestCase(
        "null_missing_with_numerics",
        docs=[{"x": 1}, {"v": 10}, {"v": 20}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 15.0}],
        msg="$avg should exclude missing fields from both sum and count",
    ),
    AccumulatorTestCase(
        "null_mixed_null_missing_with_numerics",
        docs=[{"v": None}, {"x": 1}, {"v": 30}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30.0}],
        msg="$avg should exclude both null and missing, averaging only numerics",
    ),
    AccumulatorTestCase(
        "null_remove_only",
        docs=[{"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$cond": [False, 1, "$$REMOVE"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should treat $$REMOVE as missing and return null",
    ),
]

# Property [Non-Numeric Types Ignored]: all non-numeric BSON types are
# silently ignored and excluded from both sum and count, producing null
# when no numeric values remain.
AVG_NON_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "non_numeric_string",
        docs=[{"v": "hello"}, {"v": "world"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore string values and return null",
    ),
    AccumulatorTestCase(
        "non_numeric_boolean_true",
        docs=[{"v": True}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore boolean true without coercing to numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_boolean_false",
        docs=[{"v": False}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore boolean false without coercing to numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_object",
        docs=[{"v": {"x": 1}}, {"v": {"y": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore plain objects",
    ),
    AccumulatorTestCase(
        "non_numeric_empty_object",
        docs=[{"v": {}}, {"v": {}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore empty objects",
    ),
    AccumulatorTestCase(
        "non_numeric_objectid",
        docs=[{"v": ObjectId()}, {"v": ObjectId()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore ObjectId values",
    ),
    AccumulatorTestCase(
        "non_numeric_datetime",
        docs=[
            {"v": datetime(2023, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore datetime values",
    ),
    AccumulatorTestCase(
        "non_numeric_timestamp",
        docs=[{"v": Timestamp(1, 1)}, {"v": Timestamp(2, 1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Timestamp values",
    ),
    AccumulatorTestCase(
        "non_numeric_binary",
        docs=[{"v": Binary(b"\x01")}, {"v": Binary(b"\x02")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Binary values",
    ),
    AccumulatorTestCase(
        "non_numeric_regex",
        docs=[{"v": Regex("abc")}, {"v": Regex("def")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Regex values",
    ),
    AccumulatorTestCase(
        "non_numeric_code",
        docs=[{"v": Code("x")}, {"v": Code("y")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Code values",
    ),
    AccumulatorTestCase(
        "non_numeric_minkey",
        docs=[{"v": MinKey()}, {"v": MinKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore MinKey values",
    ),
    AccumulatorTestCase(
        "non_numeric_maxkey",
        docs=[{"v": MaxKey()}, {"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore MaxKey values",
    ),
    AccumulatorTestCase(
        "non_numeric_array",
        docs=[{"v": [1, 2, 3]}, {"v": [4, 5]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore arrays without unwrapping",
    ),
    AccumulatorTestCase(
        "non_numeric_single_element_array",
        docs=[{"v": [42]}, {"v": [7]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should not unwrap single-element numeric arrays",
    ),
    AccumulatorTestCase(
        "non_numeric_empty_array",
        docs=[{"v": []}, {"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore empty arrays",
    ),
    AccumulatorTestCase(
        "non_numeric_nested_array",
        docs=[{"v": [[1, 2]]}, {"v": [[3]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore nested arrays",
    ),
    AccumulatorTestCase(
        "non_numeric_mixed_with_numerics",
        docs=[{"v": "hello"}, {"v": 10}, {"v": True}, {"v": 20}, {"v": [5]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 15.0}],
        msg="$avg should compute average only over numeric values, ignoring non-numerics",
    ),
    AccumulatorTestCase(
        "non_numeric_array_from_expression",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$literal": [1, 2, 3]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should treat array expressions as non-numeric",
    ),
]

# Property [Special Numeric Values]: NaN is numeric and propagates to the
# result, Infinity dominates finite values, Infinity + -Infinity produces
# NaN, and negative zero is not preserved.
AVG_SPECIAL_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_nan_propagates",
        docs=[{"v": FLOAT_NAN}, {"v": 5.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$avg should return NaN when any value is NaN",
    ),
    AccumulatorTestCase(
        "special_nan_over_infinity",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$avg should return NaN when group contains both NaN and Infinity",
    ),
    AccumulatorTestCase(
        "special_infinity_dominates",
        docs=[{"v": FLOAT_INFINITY}, {"v": 5.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$avg should return Infinity when Infinity dominates finite values",
    ),
    AccumulatorTestCase(
        "special_neg_infinity_dominates",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": 5.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_NEGATIVE_INFINITY}],
        msg="$avg should return -Infinity when -Infinity dominates finite values",
    ),
    AccumulatorTestCase(
        "special_inf_plus_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$avg should return NaN when group contains Infinity and -Infinity",
    ),
    AccumulatorTestCase(
        "special_neg_zero_not_preserved",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_ZERO}],
        msg="$avg should not preserve negative zero",
    ),
    AccumulatorTestCase(
        "special_decimal_neg_zero_not_preserved",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_ZERO}],
        msg="$avg should not preserve Decimal128 negative zero",
    ),
    AccumulatorTestCase(
        "special_decimal_nan_propagates",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("NaN")}],
        msg="$avg should return Decimal128 NaN when any Decimal128 value is NaN",
    ),
    AccumulatorTestCase(
        "special_decimal_nan_over_infinity",
        docs=[{"v": DECIMAL128_NAN}, {"v": DECIMAL128_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("NaN")}],
        msg="$avg should return Decimal128 NaN when group contains Decimal128 NaN and Infinity",
    ),
    AccumulatorTestCase(
        "special_decimal_infinity",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$avg should return Decimal128 Infinity when Decimal128 Infinity is present",
    ),
    AccumulatorTestCase(
        "special_decimal_neg_infinity_dominates",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_NEGATIVE_INFINITY}],
        msg="$avg should return Decimal128 -Infinity when Decimal128 -Infinity dominates",
    ),
    AccumulatorTestCase(
        "special_decimal_inf_plus_neg_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("NaN")}],
        msg="$avg should return Decimal128 NaN for Decimal128 Infinity + -Infinity",
    ),
]

# Property [Integer Boundaries]: int32 boundary values produce exact double
# results, and int64 boundary values produce double results with potential
# precision loss.
AVG_INTEGER_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "int_boundary_int32_zeros",
        docs=[{"v": 0}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_ZERO}],
        msg="$avg should return 0.0 for two int32 zeros",
    ),
    AccumulatorTestCase(
        "int_boundary_int32_one_neg_one",
        docs=[{"v": 1}, {"v": -1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_ZERO}],
        msg="$avg should return 0.0 for int32 1 and -1",
    ),
    AccumulatorTestCase(
        "int_boundary_int32_max",
        docs=[{"v": INT32_MAX}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 1_073_741_823.5}],
        msg="$avg should handle int32 MAX correctly",
    ),
    AccumulatorTestCase(
        "int_boundary_int32_min",
        docs=[{"v": INT32_MIN}, {"v": INT32_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": float(INT32_MIN)}],
        msg="$avg should handle int32 MIN correctly",
    ),
    AccumulatorTestCase(
        "int_boundary_int32_max_and_min",
        docs=[{"v": INT32_MAX}, {"v": INT32_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -0.5}],
        msg="$avg should handle int32 MAX and MIN together",
    ),
    AccumulatorTestCase(
        "int_boundary_int32_adjacent_max",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": INT32_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 2_147_483_646.5}],
        msg="$avg of adjacent int32 MAX values should produce exact double",
    ),
    AccumulatorTestCase(
        "int_boundary_int32_adjacent_min",
        docs=[{"v": INT32_MIN}, {"v": INT32_MIN + 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -2_147_483_647.5}],
        msg="$avg of adjacent int32 MIN values should produce exact double",
    ),
    AccumulatorTestCase(
        "int_boundary_int64_max",
        docs=[{"v": INT64_MAX}, {"v": INT64_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_FROM_INT64_MAX / 2}],
        msg="$avg should handle int64 MAX with precision loss in double",
    ),
    AccumulatorTestCase(
        "int_boundary_int64_min",
        docs=[{"v": INT64_MIN}, {"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -DOUBLE_FROM_INT64_MAX}],
        msg="$avg should handle int64 MIN with precision loss in double",
    ),
    AccumulatorTestCase(
        "int_boundary_int64_max_and_min",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -0.5}],
        msg="$avg should handle int64 MAX and MIN together",
    ),
    AccumulatorTestCase(
        "int_boundary_int64_adjacent_max",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_FROM_INT64_MAX}],
        msg="$avg of adjacent int64 MAX values should produce double with precision loss",
    ),
    AccumulatorTestCase(
        "int_boundary_int64_adjacent_min",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -DOUBLE_FROM_INT64_MAX}],
        msg="$avg of adjacent int64 MIN values should produce double with precision loss",
    ),
]

# Property [Float Boundaries]: subnormal, minimum normal, maximum finite,
# near-precision-limit, and whole-number double values are averaged correctly.
AVG_FLOAT_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "float_boundary_whole_number",
        docs=[{"v": 3.0}, {"v": 5.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 4.0}],
        msg="$avg should produce correct average for whole-number floats",
    ),
    AccumulatorTestCase(
        "float_boundary_subnormal_positive",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_SUBNORMAL}],
        msg="$avg should handle positive subnormal value correctly",
    ),
    AccumulatorTestCase(
        "float_boundary_subnormal_negative",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        msg="$avg should handle negative subnormal value correctly",
    ),
    AccumulatorTestCase(
        "float_boundary_subnormal_avg",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_MIN_SUBNORMAL}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_SUBNORMAL}],
        msg="$avg of two identical subnormal values should return that value",
    ),
    AccumulatorTestCase(
        "float_boundary_min_normal",
        docs=[{"v": DOUBLE_MIN_NORMAL}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MIN_NORMAL}],
        msg="$avg should handle smallest positive normal double correctly",
    ),
    AccumulatorTestCase(
        "float_boundary_max_single",
        docs=[{"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_MAX}],
        msg="$avg should handle DBL_MAX as a single value correctly",
    ),
    AccumulatorTestCase(
        "float_boundary_max_safe_integer",
        docs=[{"v": float(DOUBLE_MAX_SAFE_INTEGER)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": float(DOUBLE_MAX_SAFE_INTEGER)}],
        msg="$avg should handle max safe integer value correctly",
    ),
    AccumulatorTestCase(
        "float_boundary_max_safe_integer_avg",
        docs=[
            {"v": float(DOUBLE_MAX_SAFE_INTEGER)},
            {"v": float(DOUBLE_MAX_SAFE_INTEGER)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": float(DOUBLE_MAX_SAFE_INTEGER)}],
        msg="$avg of two max safe integer values should return that value",
    ),
    AccumulatorTestCase(
        "float_boundary_near_min",
        docs=[{"v": DOUBLE_NEAR_MIN}, {"v": DOUBLE_NEAR_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_NEAR_MIN}],
        msg="$avg should handle values near minimum normal correctly",
    ),
    AccumulatorTestCase(
        "float_boundary_near_max_single",
        docs=[{"v": DOUBLE_NEAR_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_NEAR_MAX}],
        msg="$avg should handle values near maximum finite correctly",
    ),
]

# Property [Decimal128 Behavior]: full 34-digit precision and trailing zeros
# are preserved, subnormal and near-maximum values are handled correctly, and
# values exceeding int64 range produce Decimal128 results.
AVG_DECIMAL128_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal128_full_precision",
        docs=[
            {"v": Decimal128("1.000000000000000000000000000000001")},
            {"v": Decimal128("1.000000000000000000000000000000003")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("1.000000000000000000000000000000002")}],
        msg="$avg should preserve full 34-digit Decimal128 precision",
    ),
    AccumulatorTestCase(
        "decimal128_34_digit_integer",
        docs=[
            {"v": Decimal128("1234567890123456789012345678901234")},
            {"v": Decimal128("1234567890123456789012345678901234")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("1234567890123456789012345678901234")}],
        msg="$avg should preserve 34-digit integer Decimal128 values",
    ),
    AccumulatorTestCase(
        "decimal128_trailing_zeros",
        docs=[{"v": Decimal128("2.00")}, {"v": Decimal128("4.00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("3.00")}],
        msg="$avg should preserve trailing zeros in Decimal128 results",
    ),
    AccumulatorTestCase(
        "decimal128_trailing_zeros_single_digit",
        docs=[{"v": DECIMAL128_TRAILING_ZERO}, {"v": Decimal128("3.0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("2.0")}],
        msg="$avg should preserve single trailing zero in Decimal128 results",
    ),
    AccumulatorTestCase(
        "decimal128_subnormal",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_MIN_POSITIVE}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MIN_POSITIVE}],
        msg="$avg should handle Decimal128 subnormal values correctly",
    ),
    AccumulatorTestCase(
        "decimal128_subnormal_single",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MIN_POSITIVE}],
        msg="$avg should handle a single Decimal128 subnormal value",
    ),
    AccumulatorTestCase(
        "decimal128_near_max_single",
        docs=[{"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_MAX}],
        msg="$avg should handle a single near-maximum Decimal128 value",
    ),
    AccumulatorTestCase(
        "decimal128_near_max_with_small",
        docs=[{"v": DECIMAL128_MAX}, {"v": Decimal128("1")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("5.000000000000000000000000000000000E+6144")}],
        msg="$avg should handle near-maximum Decimal128 averaged with a small value",
    ),
    AccumulatorTestCase(
        "decimal128_exceeds_int64",
        docs=[
            {"v": DECIMAL128_INT64_OVERFLOW},
            {"v": DECIMAL128_INT64_OVERFLOW},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INT64_OVERFLOW}],
        msg="$avg should produce Decimal128 for values exceeding int64 range",
    ),
]

# Property [Overflow]: sum overflow during accumulation produces Infinity for
# doubles and Decimal128, and int32/int64 overflow is handled via type
# promotion without error.
AVG_OVERFLOW_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "overflow_double_max",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$avg should return Infinity when two DBL_MAX values overflow the sum",
    ),
    AccumulatorTestCase(
        "overflow_decimal128_max",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$avg should return Decimal128 Infinity when two Decimal128 max values overflow",
    ),
    AccumulatorTestCase(
        "overflow_int32_sum",
        docs=[{"v": INT32_MAX}, {"v": INT32_MAX}, {"v": INT32_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": float(INT32_MAX)}],
        msg="$avg should handle int32 sum overflow via type promotion without error",
    ),
    AccumulatorTestCase(
        "overflow_int64_sum",
        docs=[{"v": INT64_MAX}, {"v": INT64_MAX}, {"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_FROM_INT64_MAX}],
        msg="$avg should handle int64 sum overflow by converting to double",
    ),
]

# Property [Expression Arguments]: $avg accepts any expression as its operand,
# evaluating it per-document before accumulation.
AVG_EXPRESSION_ARGS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_constant_literal",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": 5}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5.0}],
        msg="$avg should return the constant value when expression is a numeric literal",
    ),
    AccumulatorTestCase(
        "expr_nested_add",
        docs=[{"a": 2, "b": 3}, {"a": 4, "b": 6}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$add": ["$a", "$b"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 7.5}],
        msg="$avg should evaluate nested $add expression per-document before averaging",
    ),
]

# Property [Edge Cases]: a single-document group returns the value itself
# (as double or Decimal128), a single non-numeric document returns null, and
# an empty collection produces no group output.
AVG_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_int32",
        docs=[{"v": 7}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 7.0}],
        msg="$avg should return the value as double for a single int32 document",
    ),
    AccumulatorTestCase(
        "edge_single_int64",
        docs=[{"v": Int64(42)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42.0}],
        msg="$avg should return the value as double for a single int64 document",
    ),
    AccumulatorTestCase(
        "edge_single_non_numeric",
        docs=[{"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should return null for a single non-numeric document",
    ),
]

AVG_SUCCESS_TESTS = (
    AVG_NULL_MISSING_TESTS
    + AVG_NON_NUMERIC_TESTS
    + AVG_SPECIAL_NUMERIC_TESTS
    + AVG_INTEGER_BOUNDARY_TESTS
    + AVG_FLOAT_BOUNDARY_TESTS
    + AVG_DECIMAL128_TESTS
    + AVG_OVERFLOW_TESTS
    + AVG_EXPRESSION_ARGS_TESTS
    + AVG_EDGE_CASE_TESTS
)

# Property [Expression Error Propagation]: errors from sub-expressions
# propagate through $avg without being caught or suppressed.
AVG_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_prop_toint_non_convertible",
        docs=[{"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$toInt": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$avg should propagate $toInt conversion error for non-convertible value",
    ),
    AccumulatorTestCase(
        "error_prop_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$divide": ["$v", 0]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$avg should propagate $divide by zero error",
    ),
    AccumulatorTestCase(
        "error_prop_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$mod": ["$v", 0]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$avg should propagate $mod by zero error",
    ),
]

AVG_TESTS = AVG_SUCCESS_TESTS + AVG_EXPRESSION_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(AVG_TESTS))
def test_accumulator_avg(collection, test_case: AccumulatorTestCase):
    """Test $avg accumulator behavior."""
    collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_accumulator_avg_empty_collection(collection):
    """Test $avg returns no documents for an empty collection."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "result": {"$avg": "$v"}}},
                {"$project": {"_id": 0, "result": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="$avg should produce no group output for an empty collection",
    )


# Property [Return Type]: the result is double by default, but Decimal128 if
# any input value is Decimal128.
AVG_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_int32_only",
        docs=[{"v": 2}, {"v": 4}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double when all inputs are int32",
    ),
    AccumulatorTestCase(
        "type_int64_only",
        docs=[{"v": Int64(2)}, {"v": Int64(4)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double when all inputs are int64",
    ),
    AccumulatorTestCase(
        "type_int32_int64",
        docs=[{"v": 2}, {"v": Int64(4)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double for int32 and int64 mix",
    ),
    AccumulatorTestCase(
        "type_int32_double",
        docs=[{"v": 2}, {"v": 4.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double for int32 and double mix",
    ),
    AccumulatorTestCase(
        "type_int64_double",
        docs=[{"v": Int64(2)}, {"v": 4.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double for int64 and double mix",
    ),
    AccumulatorTestCase(
        "type_int32_decimal128",
        docs=[{"v": 2}, {"v": Decimal128("4")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 when any input is Decimal128",
    ),
    AccumulatorTestCase(
        "type_int64_decimal128",
        docs=[{"v": Int64(2)}, {"v": Decimal128("4")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 for int64 and Decimal128 mix",
    ),
    AccumulatorTestCase(
        "type_double_decimal128",
        docs=[{"v": 2.0}, {"v": Decimal128("4")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 for double and Decimal128 mix",
    ),
    AccumulatorTestCase(
        "type_decimal128_before_int32",
        docs=[{"v": Decimal128("4")}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 regardless of document order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(AVG_RETURN_TYPE_TESTS))
def test_accumulator_avg_return_type(collection, test_case: AccumulatorTestCase):
    """Test $avg accumulator return type."""
    collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Arity]: $avg in accumulator context is a unary operator and
# rejects array syntax in $group, $bucket, and $bucketAuto.
AVG_ARITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_multi_element_group",
        pipeline=[{"$group": {"_id": None, "result": {"$avg": ["$v", "$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject multi-element array syntax in $group",
    ),
    AccumulatorTestCase(
        "arity_empty_array_group",
        pipeline=[{"$group": {"_id": None, "result": {"$avg": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject empty array syntax in $group",
    ),
    AccumulatorTestCase(
        "arity_single_element_group",
        pipeline=[{"$group": {"_id": None, "result": {"$avg": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject single-element array syntax in $group",
    ),
    AccumulatorTestCase(
        "arity_multi_element_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$avg": ["$v", "$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject multi-element array syntax in $bucket",
    ),
    AccumulatorTestCase(
        "arity_empty_array_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$avg": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject empty array syntax in $bucket",
    ),
    AccumulatorTestCase(
        "arity_single_element_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$avg": ["$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject single-element array syntax in $bucket",
    ),
    AccumulatorTestCase(
        "arity_multi_element_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$avg": ["$v", "$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject multi-element array syntax in $bucketAuto",
    ),
    AccumulatorTestCase(
        "arity_empty_array_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$avg": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject empty array syntax in $bucketAuto",
    ),
    AccumulatorTestCase(
        "arity_single_element_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$avg": ["$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject single-element array syntax in $bucketAuto",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(AVG_ARITY_TESTS))
def test_accumulator_avg_arity(collection, test_case: AccumulatorTestCase):
    """Test $avg rejects array syntax in accumulator context."""
    collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
