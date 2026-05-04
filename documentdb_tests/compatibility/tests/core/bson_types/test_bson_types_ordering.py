"""
Tests for BSON type ordering and comparison engine behaviour.

Covers BSON type ordering (MinKey < Null < Number < String < ... < MaxKey),
string comparison semantics (Unicode NFC/NFD, null bytes, byte-level),
numeric equivalence across types (int == long == double == decimal128),
negative zero == positive zero, NaN == NaN (BSON-level equality),
Decimal128 precision (trailing zeros, scientific notation),
and field path resolution (nested, missing fields).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_NAN,
    FLOAT_NEGATIVE_NAN,
)

ADJACENT_TYPE_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minkey_lt_null",
        expression={"$lt": [MinKey(), None]},
        expected=True,
        msg="MinKey < null",
    ),
    ExpressionTestCase(
        "null_lt_int",
        expression={"$lt": [None, 0]},
        expected=True,
        msg="Null < int",
    ),
    ExpressionTestCase(
        "null_lt_long",
        expression={"$lt": [None, Int64(0)]},
        expected=True,
        msg="Null < long",
    ),
    ExpressionTestCase(
        "null_lt_double",
        expression={"$lt": [None, 0.0]},
        expected=True,
        msg="Null < double",
    ),
    ExpressionTestCase(
        "null_lt_decimal128",
        expression={"$lt": [None, Decimal128("0")]},
        expected=True,
        msg="Null < decimal128",
    ),
    ExpressionTestCase(
        "int_lt_string",
        expression={"$lt": [0, ""]},
        expected=True,
        msg="Int < string",
    ),
    ExpressionTestCase(
        "long_lt_string",
        expression={"$lt": [Int64(0), ""]},
        expected=True,
        msg="Long < string",
    ),
    ExpressionTestCase(
        "double_lt_string",
        expression={"$lt": [0.0, ""]},
        expected=True,
        msg="Double < string",
    ),
    ExpressionTestCase(
        "decimal128_lt_string",
        expression={"$lt": [Decimal128("0"), ""]},
        expected=True,
        msg="Decimal128 < string",
    ),
    ExpressionTestCase(
        "string_lt_object",
        expression={"$lt": ["", {}]},
        expected=True,
        msg="String < object",
    ),
    ExpressionTestCase(
        "object_lt_array",
        expression={"$lt": [{}, []]},
        expected=True,
        msg="Object < array",
    ),
    ExpressionTestCase(
        "array_lt_bindata",
        expression={"$lt": [[], Binary(b"", 0)]},
        expected=True,
        msg="Array < BinData",
    ),
    ExpressionTestCase(
        "bindata_lt_objectid",
        expression={"$lt": [Binary(b"", 0), ObjectId("000000000000000000000000")]},
        expected=True,
        msg="BinData < ObjectId",
    ),
    ExpressionTestCase(
        "objectid_lt_bool",
        expression={"$lt": [ObjectId("000000000000000000000000"), False]},
        expected=True,
        msg="ObjectId < bool",
    ),
    ExpressionTestCase(
        "bool_lt_date",
        expression={"$lt": [False, datetime(1970, 1, 1, tzinfo=timezone.utc)]},
        expected=True,
        msg="Bool < date",
    ),
    ExpressionTestCase(
        "date_lt_timestamp",
        expression={"$lt": [datetime(1970, 1, 1, tzinfo=timezone.utc), Timestamp(0, 0)]},
        expected=True,
        msg="Date < Timestamp",
    ),
    ExpressionTestCase(
        "timestamp_lt_regex",
        expression={"$lt": [Timestamp(0, 0), Regex("a")]},
        expected=True,
        msg="Timestamp < regex",
    ),
    ExpressionTestCase(
        "regex_lt_maxkey",
        expression={"$lt": [Regex("a"), MaxKey()]},
        expected=True,
        msg="Regex < MaxKey",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADJACENT_TYPE_ORDERING_TESTS))
def test_adjacent_type_ordering(collection, test):
    """Test BSON type ordering via $lt: MinKey < Null < Number < String < ... < MaxKey."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


NON_ADJACENT_TYPE_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_lt_object",
        expression={"$lt": [None, {}]},
        expected=True,
        msg="Null < object (skipping number and string)",
    ),
    ExpressionTestCase(
        "int_lt_bindata",
        expression={"$lt": [0, Binary(b"", 0)]},
        expected=True,
        msg="Number < BinData (skipping string, object, array)",
    ),
    ExpressionTestCase(
        "int_ne_string",
        expression={"$eq": [1, "1"]},
        expected=False,
        msg="Number not equal to string (no type coercion)",
    ),
    ExpressionTestCase(
        "int_ne_bool",
        expression={"$eq": [0, False]},
        expected=False,
        msg="Number not equal to bool (no type coercion)",
    ),
    ExpressionTestCase(
        "null_ne_bool",
        expression={"$eq": [None, False]},
        expected=False,
        msg="Null not equal to bool (no type coercion)",
    ),
    ExpressionTestCase(
        "bool_ne_int",
        expression={"$eq": [True, 1]},
        expected=False,
        msg="Bool not equal to number (no type coercion)",
    ),
    ExpressionTestCase(
        "empty_string_ne_none",
        expression={"$eq": ["", None]},
        expected=False,
        msg="Empty string not equal to null (no null coercion)",
    ),
    ExpressionTestCase(
        "zero_ne_none",
        expression={"$eq": [0, None]},
        expected=False,
        msg="Zero not equal to null (no null coercion)",
    ),
    ExpressionTestCase(
        "empty_string_ne_false",
        expression={"$eq": ["", False]},
        expected=False,
        msg="Empty string not equal to false (no falsy coercion)",
    ),
    ExpressionTestCase(
        "empty_array_ne_false",
        expression={"$eq": [[], False]},
        expected=False,
        msg="Empty array not equal to false (no falsy coercion)",
    ),
    ExpressionTestCase(
        "string_lt_timestamp",
        expression={"$lt": ["", Timestamp(0, 0)]},
        expected=True,
        msg="String < Timestamp (skipping object, array, bindata, ObjectId, bool, date)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_ADJACENT_TYPE_ORDERING_TESTS))
def test_non_adjacent_type_ordering(collection, test):
    """Test non-adjacent cross-type comparisons for transitive ordering."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


STRING_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_equal", expression={"$eq": ["abc", "abc"]}, expected=True, msg="Same strings equal"
    ),
    ExpressionTestCase(
        "str_case_sensitive",
        expression={"$eq": ["abc", "ABC"]},
        expected=False,
        msg="Case-sensitive comparison",
    ),
    ExpressionTestCase(
        "str_different",
        expression={"$eq": ["abc", "abd"]},
        expected=False,
        msg="Different strings not equal",
    ),
    ExpressionTestCase(
        "str_empty", expression={"$eq": ["", ""]}, expected=True, msg="Empty strings equal"
    ),
    ExpressionTestCase(
        "str_diff_length",
        expression={"$eq": ["abc", "abcd"]},
        expected=False,
        msg="Different length not equal",
    ),
    ExpressionTestCase(
        "str_null_byte",
        expression={"$eq": ["abc\0", "abc"]},
        expected=False,
        msg="String with null byte differs",
    ),
    ExpressionTestCase(
        "str_nfc_vs_nfd",
        expression={"$eq": ["caf\u00e9", "cafe\u0301"]},
        expected=False,
        msg="NFC and NFD normalization forms are not equal (byte-level comparison)",
    ),
    ExpressionTestCase(
        "str_emoji",
        expression={"$eq": ["\U0001f600", "\U0001f600"]},
        expected=True,
        msg="Same emoji equal",
    ),
    ExpressionTestCase(
        "str_cjk",
        expression={"$eq": ["\u4e16\u754c", "\u4e16\u754c"]},
        expected=True,
        msg="Same CJK equal",
    ),
    ExpressionTestCase(
        "str_cjk_diff",
        expression={"$eq": ["\u4e16\u754c", "\u4e16\u754d"]},
        expected=False,
        msg="Different CJK",
    ),
    ExpressionTestCase(
        "regex_flag_order",
        expression={"$eq": [Regex("abc", "im"), Regex("abc", "mi")]},
        expected=True,
        msg="Regex flags are normalized — order does not matter",
    ),
]

NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "num_int_long",
        expression={"$eq": [1, Int64(1)]},
        expected=True,
        msg="Int32(1) equals Int64(1)",
    ),
    ExpressionTestCase(
        "num_int_double",
        expression={"$eq": [1, 1.0]},
        expected=True,
        msg="Int32(1) equals Double(1.0)",
    ),
    ExpressionTestCase(
        "num_int_dec128",
        expression={"$eq": [1, Decimal128("1")]},
        expected=True,
        msg="Int32(1) equals Decimal128(1)",
    ),
    ExpressionTestCase(
        "num_long_double",
        expression={"$eq": [Int64(1), 1.0]},
        expected=True,
        msg="Int64(1) equals Double(1.0)",
    ),
    ExpressionTestCase(
        "num_long_dec128",
        expression={"$eq": [Int64(1), Decimal128("1")]},
        expected=True,
        msg="Int64(1) equals Decimal128(1)",
    ),
    ExpressionTestCase(
        "num_double_dec128",
        expression={"$eq": [1.0, Decimal128("1")]},
        expected=True,
        msg="Double(1.0) equals Decimal128(1)",
    ),
    ExpressionTestCase(
        "num_zero_int_long",
        expression={"$eq": [0, Int64(0)]},
        expected=True,
        msg="Int32(0) equals Int64(0)",
    ),
    ExpressionTestCase(
        "num_zero_int_double",
        expression={"$eq": [0, 0.0]},
        expected=True,
        msg="Int32(0) equals Double(0.0)",
    ),
    ExpressionTestCase(
        "num_zero_double_dec128",
        expression={"$eq": [0.0, Decimal128("0")]},
        expected=True,
        msg="Double(0.0) equals Decimal128(0)",
    ),
]

NEGATIVE_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "negzero_double",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, 0.0]},
        expected=True,
        msg="-0.0 equals 0.0",
    ),
    ExpressionTestCase(
        "negzero_dec128",
        expression={"$eq": [DECIMAL128_NEGATIVE_ZERO, DECIMAL128_ZERO]},
        expected=True,
        msg="Decimal128(-0) equals Decimal128(0)",
    ),
    ExpressionTestCase(
        "negzero_int",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, 0]},
        expected=True,
        msg="-0.0 equals Int32(0)",
    ),
    ExpressionTestCase(
        "negzero_long",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, Int64(0)]},
        expected=True,
        msg="-0.0 equals Int64(0)",
    ),
    ExpressionTestCase(
        "negzero_cross_dec128",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, Decimal128("0")]},
        expected=True,
        msg="-0.0 equals Decimal128(0)",
    ),
]

NAN_EQUALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_nan", expression={"$eq": [FLOAT_NAN, FLOAT_NAN]}, expected=True, msg="NaN equals NaN"
    ),
    ExpressionTestCase(
        "nan_negative_nan",
        expression={"$eq": [FLOAT_NAN, FLOAT_NEGATIVE_NAN]},
        expected=True,
        msg="NaN equals NaN",
    ),
    ExpressionTestCase(
        "nan_int", expression={"$eq": [FLOAT_NAN, 1]}, expected=False, msg="NaN not equal to int"
    ),
    ExpressionTestCase(
        "nan_null",
        expression={"$eq": [FLOAT_NAN, None]},
        expected=False,
        msg="NaN not equal to null",
    ),
    ExpressionTestCase(
        "nan_dec_nan",
        expression={"$eq": [DECIMAL128_NAN, DECIMAL128_NAN]},
        expected=True,
        msg="Decimal128 NaN equals Decimal128 NaN",
    ),
    ExpressionTestCase(
        "dec_nan_negative_dec_nan",
        expression={"$eq": [DECIMAL128_NAN, DECIMAL128_NEGATIVE_NAN]},
        expected=True,
        msg="Decimal128 NaN equals Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_cross_type",
        expression={"$eq": [FLOAT_NAN, DECIMAL128_NAN]},
        expected=True,
        msg="Cross-type NaN equality",
    ),
]

DECIMAL128_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec_trailing_zeros",
        expression={"$eq": [Decimal128("1.0"), Decimal128("1.00")]},
        expected=True,
        msg="Trailing zeros are equal",
    ),
    ExpressionTestCase(
        "dec_scientific",
        expression={"$eq": [Decimal128("1E+2"), Decimal128("100")]},
        expected=True,
        msg="Scientific notation equals standard",
    ),
    ExpressionTestCase(
        "dec_zero_diff_exp",
        expression={"$eq": [Decimal128("0E-6176"), Decimal128("0")]},
        expected=True,
        msg="Zero with different exponents are equal",
    ),
    ExpressionTestCase(
        "dec_zero_extreme_exp",
        expression={"$eq": [Decimal128("0E-6176"), Decimal128("0E+6111")]},
        expected=True,
        msg="Zero with extreme exponent range are equal",
    ),
]

MINKEY_MAXKEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minkey_eq_minkey",
        expression={"$eq": [MinKey(), MinKey()]},
        expected=True,
        msg="MinKey equals MinKey",
    ),
    ExpressionTestCase(
        "maxkey_eq_maxkey",
        expression={"$eq": [MaxKey(), MaxKey()]},
        expected=True,
        msg="MaxKey equals MaxKey",
    ),
    ExpressionTestCase(
        "minkey_ne_maxkey",
        expression={"$eq": [MinKey(), MaxKey()]},
        expected=False,
        msg="MinKey not equal to MaxKey",
    ),
]

ALL_LITERAL_TESTS = (
    STRING_COMPARISON_TESTS
    + NUMERIC_EQUIVALENCE_TESTS
    + NEGATIVE_ZERO_TESTS
    + NAN_EQUALITY_TESTS
    + DECIMAL128_PRECISION_TESTS
    + MINKEY_MAXKEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_LITERAL_TESTS))
def test_bson_comparison_engine(collection, test):
    """Test BSON comparison engine: strings, numerics, NaN, Decimal128."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "fp_simple",
        expression={"$eq": ["$a", 1]},
        doc={"a": 1},
        expected=True,
        msg="Simple field lookup",
    ),
    ExpressionTestCase(
        "fp_nested",
        expression={"$eq": ["$a.b", 1]},
        doc={"a": {"b": 1}},
        expected=True,
        msg="Nested field lookup",
    ),
    ExpressionTestCase(
        "fp_deep",
        expression={"$eq": ["$a.b.c.d.e", 1]},
        doc={"a": {"b": {"c": {"d": {"e": 1}}}}},
        expected=True,
        msg="Deeply nested field lookup",
    ),
    ExpressionTestCase(
        "fp_missing_vs_null",
        expression={"$eq": ["$missing", None]},
        doc={"a": 1},
        expected=False,
        msg="Missing field not equal to null literal",
    ),
    ExpressionTestCase(
        "fp_missing_nested",
        expression={"$eq": ["$x.y.z", None]},
        doc={},
        expected=False,
        msg="Missing nested field not equal to null literal",
    ),
]

ALL_INSERT_TESTS = FIELD_PATH_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_bson_field_path_resolution(collection, test):
    """Test field path resolution: nested, missing fields."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
