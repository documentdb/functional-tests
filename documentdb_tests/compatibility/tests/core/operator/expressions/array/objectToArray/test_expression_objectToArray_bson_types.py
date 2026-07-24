"""
BSON type tests for $objectToArray expression.

Tests that various BSON value types are preserved when converting
objects to k/v arrays, including special numeric values, boundary values,
UUID binary, and nested BSON values.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Literal-path parity]: representative cases also run through the
# literal-value path, defined by name (not positional index) and appended to
# ALL_BSON_TESTS below for insert coverage too. Also holds the sole mixed-types
# case.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="value_int64",
        doc={"obj": {"a": Int64(99)}},
        expected=[{"k": "a", "v": Int64(99)}],
        msg="Should preserve Int64 value",
    ),
    ExpressionTestCase(
        id="value_binary",
        doc={"obj": {"a": Binary(b"\x01\x02", 0)}},
        expected=[{"k": "a", "v": b"\x01\x02"}],
        msg="Should preserve Binary value",
    ),
    ExpressionTestCase(
        id="value_uuid",
        doc={"obj": {"a": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))}},
        expected=[{"k": "a", "v": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))}],
        msg="Should preserve UUID binary value",
    ),
    ExpressionTestCase(
        id="value_infinity",
        doc={"obj": {"a": FLOAT_INFINITY}},
        expected=[{"k": "a", "v": FLOAT_INFINITY}],
        msg="Should preserve Infinity value",
    ),
    ExpressionTestCase(
        id="value_int32_max",
        doc={"obj": {"a": INT32_MAX}},
        expected=[{"k": "a", "v": INT32_MAX}],
        msg="Should preserve INT32_MAX value",
    ),
    ExpressionTestCase(
        id="nested_bson_in_object_value",
        doc={"obj": {"a": {"x": Int64(1), "y": Decimal128("2.5")}}},
        expected=[{"k": "a", "v": {"x": Int64(1), "y": Decimal128("2.5")}}],
        msg="Should preserve nested BSON types in object value",
    ),
    ExpressionTestCase(
        id="mixed_bson_types",
        doc={
            "obj": {
                "int64": Int64(1),
                "dec": Decimal128("1.5"),
                "dt": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "oid": ObjectId("000000000000000000000001"),
                "bin": Binary(b"\x01", 0),
                "ts": Timestamp(0, 0),
                "min": MinKey(),
            }
        },
        expected=[
            {"k": "int64", "v": Int64(1)},
            {"k": "dec", "v": Decimal128("1.5")},
            {"k": "dt", "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"k": "oid", "v": ObjectId("000000000000000000000001")},
            {"k": "bin", "v": b"\x01"},
            {"k": "ts", "v": Timestamp(0, 0)},
            {"k": "min", "v": MinKey()},
        ],
        msg="Should preserve multiple mixed BSON types in one conversion",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_objectToArray_bson_literal(collection, test):
    """Test $objectToArray BSON types with literal values."""
    result = execute_expression(collection, {"$objectToArray": test.doc["obj"]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [BSON type preservation]: each non-object BSON value type survives
# the object→array conversion unchanged — no coercion, widening, or precision
# loss (e.g. Binary subtype 0 decodes to bytes, UUID binary round-trips exactly).
BSON_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="value_decimal128",
        doc={"obj": {"a": Decimal128("3.14")}},
        expected=[{"k": "a", "v": Decimal128("3.14")}],
        msg="Should preserve Decimal128 value",
    ),
    ExpressionTestCase(
        id="value_datetime",
        doc={"obj": {"a": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        expected=[{"k": "a", "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="Should preserve datetime value",
    ),
    ExpressionTestCase(
        id="value_objectid",
        doc={"obj": {"a": ObjectId("000000000000000000000001")}},
        expected=[{"k": "a", "v": ObjectId("000000000000000000000001")}],
        msg="Should preserve ObjectId value",
    ),
    ExpressionTestCase(
        id="value_bool_false",
        doc={"obj": {"a": False}},
        expected=[{"k": "a", "v": False}],
        msg="Should preserve false value",
    ),
    ExpressionTestCase(
        id="value_bool_true",
        doc={"obj": {"a": True}},
        expected=[{"k": "a", "v": True}],
        msg="Should preserve true value",
    ),
    ExpressionTestCase(
        id="value_regex",
        doc={"obj": {"a": Regex("^abc", "i")}},
        expected=[{"k": "a", "v": Regex("^abc", "i")}],
        msg="Should preserve regex value",
    ),
    ExpressionTestCase(
        id="value_minkey",
        doc={"obj": {"a": MinKey()}},
        expected=[{"k": "a", "v": MinKey()}],
        msg="Should preserve MinKey value",
    ),
    ExpressionTestCase(
        id="value_maxkey",
        doc={"obj": {"a": MaxKey()}},
        expected=[{"k": "a", "v": MaxKey()}],
        msg="Should preserve MaxKey value",
    ),
    ExpressionTestCase(
        id="value_timestamp",
        doc={"obj": {"a": Timestamp(1234567890, 1)}},
        expected=[{"k": "a", "v": Timestamp(1234567890, 1)}],
        msg="Should preserve Timestamp value",
    ),
    ExpressionTestCase(
        id="value_code",
        doc={"obj": {"a": Code("x")}},
        expected=[{"k": "a", "v": Code("x")}],
        msg="Should preserve JavaScript Code value",
    ),
]

# Property [Special numeric values]: IEEE-754/Decimal128 special values
# (±Infinity, ±0, NaN, full precision, exponent/trailing-zero notation,
# subnormal zero) pass through without normalization.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="value_neg_infinity",
        doc={"obj": {"a": FLOAT_NEGATIVE_INFINITY}},
        expected=[{"k": "a", "v": FLOAT_NEGATIVE_INFINITY}],
        msg="Should preserve -Infinity value",
    ),
    ExpressionTestCase(
        id="value_neg_zero",
        doc={"obj": {"a": DOUBLE_NEGATIVE_ZERO}},
        expected=[{"k": "a", "v": DOUBLE_NEGATIVE_ZERO}],
        msg="Should preserve negative zero value",
    ),
    ExpressionTestCase(
        id="value_decimal128_nan",
        doc={"obj": {"a": DECIMAL128_NAN}},
        expected=[{"k": "a", "v": DECIMAL128_NAN}],
        msg="Should preserve Decimal128 NaN value",
    ),
    ExpressionTestCase(
        id="value_decimal128_infinity",
        doc={"obj": {"a": DECIMAL128_INFINITY}},
        expected=[{"k": "a", "v": DECIMAL128_INFINITY}],
        msg="Should preserve Decimal128 Infinity value",
    ),
    ExpressionTestCase(
        id="value_decimal128_neg_infinity",
        doc={"obj": {"a": DECIMAL128_NEGATIVE_INFINITY}},
        expected=[{"k": "a", "v": DECIMAL128_NEGATIVE_INFINITY}],
        msg="Should preserve Decimal128 -Infinity value",
    ),
    ExpressionTestCase(
        id="value_decimal128_neg_zero",
        doc={"obj": {"a": DECIMAL128_NEGATIVE_ZERO}},
        expected=[{"k": "a", "v": DECIMAL128_NEGATIVE_ZERO}],
        msg="Should preserve Decimal128 -0 value",
    ),
    ExpressionTestCase(
        id="value_decimal128_high_precision",
        doc={"obj": {"a": Decimal128("1.234567890123456789012345678901234")}},
        expected=[{"k": "a", "v": Decimal128("1.234567890123456789012345678901234")}],
        msg="Should preserve full Decimal128 precision",
    ),
    ExpressionTestCase(
        id="value_decimal128_zero_exponent",
        doc={"obj": {"a": Decimal128("0E+10")}},
        expected=[{"k": "a", "v": Decimal128("0E+10")}],
        msg="Should preserve Decimal128 exponent notation",
    ),
    ExpressionTestCase(
        id="value_decimal128_trailing_zeros",
        doc={"obj": {"a": Decimal128("1.00000")}},
        expected=[{"k": "a", "v": Decimal128("1.00000")}],
        msg="Should preserve Decimal128 trailing zeros",
    ),
    ExpressionTestCase(
        id="value_decimal128_subnormal_zero",
        doc={"obj": {"a": Decimal128("0E-6176")}},
        expected=[{"k": "a", "v": Decimal128("0E-6176")}],
        msg="Should preserve Decimal128 subnormal zero",
    ),
]

# Property [Boundary values]: min/max values for each numeric BSON type
# (Int32, Int64, Decimal128) are preserved exactly at the boundary.
BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="value_int32_min",
        doc={"obj": {"a": INT32_MIN}},
        expected=[{"k": "a", "v": INT32_MIN}],
        msg="Should preserve INT32_MIN value",
    ),
    ExpressionTestCase(
        id="value_int64_max",
        doc={"obj": {"a": INT64_MAX}},
        expected=[{"k": "a", "v": INT64_MAX}],
        msg="Should preserve INT64_MAX value",
    ),
    ExpressionTestCase(
        id="value_int64_min",
        doc={"obj": {"a": INT64_MIN}},
        expected=[{"k": "a", "v": INT64_MIN}],
        msg="Should preserve INT64_MIN value",
    ),
    ExpressionTestCase(
        id="value_decimal128_max",
        doc={"obj": {"a": DECIMAL128_MAX}},
        expected=[{"k": "a", "v": DECIMAL128_MAX}],
        msg="Should preserve DECIMAL128_MAX value",
    ),
    ExpressionTestCase(
        id="value_decimal128_min",
        doc={"obj": {"a": DECIMAL128_MIN}},
        expected=[{"k": "a", "v": DECIMAL128_MIN}],
        msg="Should preserve DECIMAL128_MIN value",
    ),
]

# Property [Nested BSON types]: BSON-typed values nested inside an object or
# array value (not just at the top level) retain their exact type through the
# conversion, at any nesting depth.
NESTED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_bson_in_array_value",
        doc={
            "obj": {
                "a": [
                    MinKey(),
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                    ObjectId("000000000000000000000001"),
                ]
            }
        },
        expected=[
            {
                "k": "a",
                "v": [
                    MinKey(),
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                    ObjectId("000000000000000000000001"),
                ],
            }
        ],
        msg="Should preserve nested BSON types in array value",
    ),
    ExpressionTestCase(
        id="deeply_nested_bson",
        doc={"obj": {"a": {"x": [{"y": Decimal128("1.5")}, Timestamp(0, 0)]}}},
        expected=[{"k": "a", "v": {"x": [{"y": Decimal128("1.5")}, Timestamp(0, 0)]}}],
        msg="Should preserve deeply nested BSON types",
    ),
]

ALL_BSON_TESTS = (
    BSON_VALUE_TESTS
    + SPECIAL_NUMERIC_TESTS
    + BOUNDARY_TESTS
    + NESTED_BSON_TESTS
    + TEST_SUBSET_FOR_LITERAL
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_objectToArray_bson_insert(collection, test):
    """Test $objectToArray BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, {"$objectToArray": "$obj"}, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
