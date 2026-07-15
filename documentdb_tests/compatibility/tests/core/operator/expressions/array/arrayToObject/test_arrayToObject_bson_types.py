"""
BSON type tests for $arrayToObject expression.

Tests that various BSON value types are preserved when converting
arrays to objects, including special numeric values, boundary values,
UUID binary, nested BSON values, and numeric type equivalence,
across both k/v and pair input forms.
"""

import math
from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Value Types K/V]: $arrayToObject preserves each value's BSON type in k/v form.
BSON_KV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="kv_int64",
        doc={"arr": [{"k": "a", "v": Int64(99)}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Int64(99)},
        msg="$arrayToObject should preserve Int64 value",
    ),
    ExpressionTestCase(
        id="kv_decimal128",
        doc={"arr": [{"k": "a", "v": Decimal128("3.14")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Decimal128("3.14")},
        msg="$arrayToObject should preserve Decimal128 value",
    ),
    ExpressionTestCase(
        id="kv_datetime",
        doc={"arr": [{"k": "a", "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="$arrayToObject should preserve datetime value",
    ),
    ExpressionTestCase(
        id="kv_objectid",
        doc={"arr": [{"k": "a", "v": ObjectId("000000000000000000000001")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": ObjectId("000000000000000000000001")},
        msg="$arrayToObject should preserve ObjectId value",
    ),
    ExpressionTestCase(
        id="kv_bool_false",
        doc={"arr": [{"k": "a", "v": False}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": False},
        msg="$arrayToObject should preserve false value",
    ),
    ExpressionTestCase(
        id="kv_bool_true",
        doc={"arr": [{"k": "a", "v": True}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": True},
        msg="$arrayToObject should preserve true value",
    ),
    ExpressionTestCase(
        id="kv_null",
        doc={"arr": [{"k": "a", "v": None}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": None},
        msg="$arrayToObject should preserve null value",
    ),
    ExpressionTestCase(
        id="kv_regex",
        doc={"arr": [{"k": "a", "v": Regex("^abc", "i")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Regex("^abc", "i")},
        msg="$arrayToObject should preserve regex value",
    ),
    ExpressionTestCase(
        id="kv_minkey",
        doc={"arr": [{"k": "a", "v": MinKey()}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": MinKey()},
        msg="$arrayToObject should preserve MinKey value",
    ),
    ExpressionTestCase(
        id="kv_maxkey",
        doc={"arr": [{"k": "a", "v": MaxKey()}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": MaxKey()},
        msg="$arrayToObject should preserve MaxKey value",
    ),
    ExpressionTestCase(
        id="kv_binary",
        doc={"arr": [{"k": "a", "v": Binary(b"\x01\x02\x03", 0)}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": b"\x01\x02\x03"},
        msg="$arrayToObject should preserve Binary value",
    ),
    ExpressionTestCase(
        id="kv_timestamp",
        doc={"arr": [{"k": "a", "v": Timestamp(1234567890, 1)}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Timestamp(1234567890, 1)},
        msg="$arrayToObject should preserve Timestamp value",
    ),
    ExpressionTestCase(
        id="kv_uuid",
        doc={
            "arr": [{"k": "a", "v": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))}]
        },
        expression={"$arrayToObject": "$arr"},
        expected={"a": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))},
        msg="$arrayToObject should preserve UUID binary value",
    ),
]

# Property [Value Types Pair]: $arrayToObject preserves each value's BSON type in pair form.
BSON_PAIR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="pair_int64",
        doc={"arr": [["a", Int64(99)]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Int64(99)},
        msg="$arrayToObject should preserve Int64 value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_decimal128",
        doc={"arr": [["a", Decimal128("3.14")]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Decimal128("3.14")},
        msg="$arrayToObject should preserve Decimal128 value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_datetime",
        doc={"arr": [["a", datetime(2024, 1, 1, tzinfo=timezone.utc)]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="$arrayToObject should preserve datetime value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_objectid",
        doc={"arr": [["a", ObjectId("000000000000000000000001")]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": ObjectId("000000000000000000000001")},
        msg="$arrayToObject should preserve ObjectId value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_binary",
        doc={"arr": [["a", Binary(b"\x01\x02\x03", 0)]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": b"\x01\x02\x03"},
        msg="$arrayToObject should preserve Binary value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_timestamp",
        doc={"arr": [["a", Timestamp(1234567890, 1)]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Timestamp(1234567890, 1)},
        msg="$arrayToObject should preserve Timestamp value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_regex",
        doc={"arr": [["a", Regex("^abc", "i")]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Regex("^abc", "i")},
        msg="$arrayToObject should preserve regex value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_minkey",
        doc={"arr": [["a", MinKey()]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": MinKey()},
        msg="$arrayToObject should preserve MinKey value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_maxkey",
        doc={"arr": [["a", MaxKey()]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": MaxKey()},
        msg="$arrayToObject should preserve MaxKey value (pair form)",
    ),
    ExpressionTestCase(
        id="pair_uuid",
        doc={"arr": [["a", Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))},
        msg="$arrayToObject should preserve UUID binary value (pair form)",
    ),
]

# Property [Special Numerics]: $arrayToObject preserves NaN, Infinity, and negative zero.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="value_infinity",
        doc={"arr": [{"k": "a", "v": FLOAT_INFINITY}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": FLOAT_INFINITY},
        msg="$arrayToObject should preserve Infinity value",
    ),
    ExpressionTestCase(
        id="value_neg_infinity",
        doc={"arr": [{"k": "a", "v": FLOAT_NEGATIVE_INFINITY}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": FLOAT_NEGATIVE_INFINITY},
        msg="$arrayToObject should preserve -Infinity value",
    ),
    ExpressionTestCase(
        id="value_neg_zero",
        doc={"arr": [{"k": "a", "v": DOUBLE_NEGATIVE_ZERO}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": DOUBLE_NEGATIVE_ZERO},
        msg="$arrayToObject should preserve negative zero value",
    ),
    ExpressionTestCase(
        id="value_decimal128_nan",
        doc={"arr": [{"k": "a", "v": DECIMAL128_NAN}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": DECIMAL128_NAN},
        msg="$arrayToObject should preserve Decimal128 NaN value",
    ),
    ExpressionTestCase(
        id="value_decimal128_infinity",
        doc={"arr": [{"k": "a", "v": DECIMAL128_INFINITY}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": DECIMAL128_INFINITY},
        msg="$arrayToObject should preserve Decimal128 Infinity value",
    ),
    ExpressionTestCase(
        id="value_decimal128_neg_infinity",
        doc={"arr": [{"k": "a", "v": DECIMAL128_NEGATIVE_INFINITY}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": DECIMAL128_NEGATIVE_INFINITY},
        msg="$arrayToObject should preserve Decimal128 -Infinity value",
    ),
    ExpressionTestCase(
        id="value_decimal128_neg_zero",
        doc={"arr": [{"k": "a", "v": DECIMAL128_NEGATIVE_ZERO}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": DECIMAL128_NEGATIVE_ZERO},
        msg="$arrayToObject should preserve Decimal128 -0 value",
    ),
    ExpressionTestCase(
        id="value_decimal128_high_precision",
        doc={"arr": [{"k": "a", "v": Decimal128("1.234567890123456789012345678901234")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Decimal128("1.234567890123456789012345678901234")},
        msg="$arrayToObject should preserve full Decimal128 precision",
    ),
    ExpressionTestCase(
        id="value_decimal128_zero_exponent",
        doc={"arr": [{"k": "a", "v": Decimal128("0E+10")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Decimal128("0E+10")},
        msg="$arrayToObject should preserve Decimal128 exponent notation",
    ),
    ExpressionTestCase(
        id="value_decimal128_trailing_zeros",
        doc={"arr": [{"k": "a", "v": Decimal128("1.00000")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Decimal128("1.00000")},
        msg="$arrayToObject should preserve Decimal128 trailing zeros",
    ),
    ExpressionTestCase(
        id="value_decimal128_subnormal_zero",
        doc={"arr": [{"k": "a", "v": Decimal128("0E-6176")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Decimal128("0E-6176")},
        msg="$arrayToObject should preserve Decimal128 subnormal zero",
    ),
]

# Property [Numeric Boundaries]: $arrayToObject preserves numeric boundary values.
BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="value_int32_max",
        doc={"arr": [{"k": "a", "v": INT32_MAX}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": INT32_MAX},
        msg="$arrayToObject should preserve INT32_MAX value",
    ),
    ExpressionTestCase(
        id="value_int32_min",
        doc={"arr": [{"k": "a", "v": INT32_MIN}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": INT32_MIN},
        msg="$arrayToObject should preserve INT32_MIN value",
    ),
    ExpressionTestCase(
        id="value_int64_max",
        doc={"arr": [{"k": "a", "v": INT64_MAX}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": INT64_MAX},
        msg="$arrayToObject should preserve INT64_MAX value",
    ),
    ExpressionTestCase(
        id="value_int64_min",
        doc={"arr": [{"k": "a", "v": INT64_MIN}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": INT64_MIN},
        msg="$arrayToObject should preserve INT64_MIN value",
    ),
    ExpressionTestCase(
        id="value_decimal128_max",
        doc={"arr": [{"k": "a", "v": DECIMAL128_MAX}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": DECIMAL128_MAX},
        msg="$arrayToObject should preserve DECIMAL128_MAX value",
    ),
    ExpressionTestCase(
        id="value_decimal128_min",
        doc={"arr": [{"k": "a", "v": DECIMAL128_MIN}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": DECIMAL128_MIN},
        msg="$arrayToObject should preserve DECIMAL128_MIN value",
    ),
]

# Property [Nested Values]: $arrayToObject preserves nested arrays and documents as values.
NESTED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_bson_in_object_value",
        doc={"arr": [{"k": "a", "v": {"x": Int64(1), "y": DECIMAL128_TWO_AND_HALF}}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": {"x": Int64(1), "y": DECIMAL128_TWO_AND_HALF}},
        msg="$arrayToObject should preserve nested BSON types in object value",
    ),
    ExpressionTestCase(
        id="nested_bson_in_array_value",
        doc={
            "arr": [
                {
                    "k": "a",
                    "v": [
                        MinKey(),
                        datetime(2024, 1, 1, tzinfo=timezone.utc),
                        ObjectId("000000000000000000000001"),
                    ],
                }
            ]
        },
        expression={"$arrayToObject": "$arr"},
        expected={
            "a": [
                MinKey(),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                ObjectId("000000000000000000000001"),
            ]
        },
        msg="$arrayToObject should preserve nested BSON types in array value",
    ),
    ExpressionTestCase(
        id="deeply_nested_bson",
        doc={"arr": [{"k": "a", "v": {"x": [{"y": DECIMAL128_ONE_AND_HALF}, Timestamp(0, 0)]}}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": {"x": [{"y": DECIMAL128_ONE_AND_HALF}, Timestamp(0, 0)]}},
        msg="$arrayToObject should preserve deeply nested BSON types",
    ),
    ExpressionTestCase(
        id="nested_array_not_interpreted_as_kv",
        doc={"arr": [{"k": "a", "v": [["level2", {"x": 1}]]}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": [["level2", {"x": 1}]]},
        msg="$arrayToObject should preserve nested array as value without interpreting as k/v",
    ),
]

# Property [Duplicate Numeric Keys]: last value wins for duplicate keys of differing numeric types.
NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="duplicate_key_int_then_int64",
        doc={"arr": [{"k": "a", "v": 1}, {"k": "a", "v": Int64(2)}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Int64(2)},
        msg="$arrayToObject should keep the last Int64 value for a duplicate key",
    ),
    ExpressionTestCase(
        id="duplicate_key_int_then_decimal128",
        doc={"arr": [{"k": "a", "v": 1}, {"k": "a", "v": Decimal128("2")}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": Decimal128("2")},
        msg="$arrayToObject should keep the last Decimal128 value for a duplicate key",
    ),
    ExpressionTestCase(
        id="duplicate_key_decimal128_then_double",
        doc={"arr": [{"k": "a", "v": Decimal128("1")}, {"k": "a", "v": 2.0}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 2.0},
        msg="$arrayToObject should keep the last double value for a duplicate key",
    ),
]

# Property [Mixed Types]: $arrayToObject preserves multiple mixed BSON value types in one array.
MIXED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="kv_mixed_bson_types",
        doc={
            "arr": [
                {"k": "int64", "v": Int64(1)},
                {"k": "dec", "v": DECIMAL128_ONE_AND_HALF},
                {"k": "dt", "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
                {"k": "oid", "v": ObjectId("000000000000000000000001")},
                {"k": "bin", "v": Binary(b"\x01", 0)},
                {"k": "ts", "v": Timestamp(0, 0)},
                {"k": "min", "v": MinKey()},
            ]
        },
        expression={"$arrayToObject": "$arr"},
        expected={
            "int64": Int64(1),
            "dec": DECIMAL128_ONE_AND_HALF,
            "dt": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "oid": ObjectId("000000000000000000000001"),
            "bin": b"\x01",
            "ts": Timestamp(0, 0),
            "min": MinKey(),
        },
        msg="$arrayToObject should preserve multiple mixed BSON types in one conversion",
    ),
]

ALL_BSON_TESTS = (
    BSON_KV_TESTS
    + BSON_PAIR_TESTS
    + SPECIAL_NUMERIC_TESTS
    + BOUNDARY_TESTS
    + NESTED_BSON_TESTS
    + NUMERIC_EQUIVALENCE_TESTS
    + MIXED_BSON_TESTS
)


# Float NaN needs a dedicated test because NaN does not compare equal to itself.
def test_arrayToObject_float_nan_value(collection):
    """Test $arrayToObject preserves float NaN value."""
    result = execute_expression(collection, {"$arrayToObject": {"$literal": [["a", FLOAT_NAN]]}})
    assert_expression_result(
        result,
        expected={"a": pytest.approx(math.nan, nan_ok=True)},
        msg="$arrayToObject should preserve a NaN value",
    )
