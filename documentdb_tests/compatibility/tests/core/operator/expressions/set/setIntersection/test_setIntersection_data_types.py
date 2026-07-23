"""Tests for $setIntersection element type handling, numeric equivalence, and special values."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [Element Type Coverage]: arrays of any single BSON element type
# intersect by value.
SETINTERSECTION_ELEMENT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_elements",
        doc={"a": [10, 20, 30], "b": [20, 30, 40]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[20, 30],
        msg="$setIntersection should intersect int arrays",
    ),
    ExpressionTestCase(
        "long_elements",
        doc={"a": [Int64(1), Int64(2)], "b": [Int64(2), Int64(3)]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Int64(2)],
        msg="$setIntersection should intersect long arrays",
    ),
    ExpressionTestCase(
        "double_elements",
        doc={"a": [1.0, 2.0], "b": [2.0, 3.0]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[2.0],
        msg="$setIntersection should intersect double arrays",
    ),
    ExpressionTestCase(
        "decimal128_elements",
        doc={"a": [Decimal128("1"), Decimal128("2")], "b": [Decimal128("2"), Decimal128("3")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Decimal128("2")],
        msg="$setIntersection should intersect decimal128 arrays",
    ),
    ExpressionTestCase(
        "string_elements",
        doc={"a": ["a", "b", "c"], "b": ["b", "c", "d"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["b", "c"],
        msg="$setIntersection should intersect string arrays",
    ),
    ExpressionTestCase(
        "bool_true",
        doc={"a": [True, False], "b": [True]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[True],
        msg="$setIntersection should intersect boolean true",
    ),
    ExpressionTestCase(
        "bool_false",
        doc={"a": [True, False], "b": [False]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[False],
        msg="$setIntersection should intersect boolean false",
    ),
    ExpressionTestCase(
        "null_elements",
        doc={"a": [None, 1], "b": [None, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[None],
        msg="$setIntersection should intersect null elements",
    ),
    ExpressionTestCase(
        "minkey_elements",
        doc={"a": [MinKey(), 1], "b": [MinKey(), 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[MinKey()],
        msg="$setIntersection should intersect MinKey elements",
    ),
    ExpressionTestCase(
        "maxkey_elements",
        doc={"a": [MaxKey(), 1], "b": [MaxKey(), 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[MaxKey()],
        msg="$setIntersection should intersect MaxKey elements",
    ),
    ExpressionTestCase(
        "date_elements",
        doc={
            "a": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            ],
            "b": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        },
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[datetime(2024, 1, 1, tzinfo=timezone.utc)],
        msg="$setIntersection should intersect matching date elements",
    ),
    ExpressionTestCase(
        "objectid_elements",
        doc={
            "a": [
                ObjectId("507f1f77bcf86cd799439011"),
                ObjectId("507f191e810c19729de860ea"),
            ],
            "b": [ObjectId("507f1f77bcf86cd799439011")],
        },
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[ObjectId("507f1f77bcf86cd799439011")],
        msg="$setIntersection should intersect matching ObjectId elements",
    ),
    ExpressionTestCase(
        "timestamp_elements",
        doc={"a": [Timestamp(100, 1), Timestamp(200, 1)], "b": [Timestamp(100, 1)]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Timestamp(100, 1)],
        msg="$setIntersection should intersect matching Timestamp elements",
    ),
    ExpressionTestCase(
        "regex_elements",
        doc={"a": [Regex("abc", "i"), Regex("def", "")], "b": [Regex("abc", "i")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Regex("abc", "i")],
        msg="$setIntersection should intersect matching regex elements",
    ),
    ExpressionTestCase(
        "javascript_elements",
        doc={"a": [Code("function(){}"), Code("other()")], "b": [Code("function(){}")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Code("function(){}")],
        msg="$setIntersection should intersect matching javascript code elements",
    ),
    ExpressionTestCase(
        "binary_elements",
        doc={"a": [Binary(b"\x00\x00\x00", 0)], "b": [Binary(b"\x00\x00\x00", 0)]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[b"\x00\x00\x00"],
        msg="$setIntersection should intersect matching binary elements",
    ),
    ExpressionTestCase(
        "object_same",
        doc={"a": [{"a": 1}, {"b": 2}], "b": [{"a": 1}, {"c": 3}]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[{"a": 1}],
        msg="$setIntersection should match identical objects",
    ),
    ExpressionTestCase(
        "object_nested",
        doc={"a": [{"a": {"b": 1}}], "b": [{"a": {"b": 1}}]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[{"a": {"b": 1}}],
        msg="$setIntersection should match nested objects",
    ),
    ExpressionTestCase(
        "empty_objects",
        doc={"a": [{}], "b": [{}]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[{}],
        msg="$setIntersection should match empty objects",
    ),
]

# Property [Within-Type Distinction]: near-equal values of the same type are
# distinct and do not match.
SETINTERSECTION_DISTINCTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_diff_ms",
        doc={
            "a": [datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)],
            "b": [datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)],
        },
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for dates differing by milliseconds",
    ),
    ExpressionTestCase(
        "timestamp_diff_ordinal",
        doc={"a": [Timestamp(100, 1)], "b": [Timestamp(100, 2)]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for timestamps differing by ordinal",
    ),
    ExpressionTestCase(
        "regex_diff_flags",
        doc={"a": [Regex("abc", "i")], "b": [Regex("abc", "")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for regex differing by flags",
    ),
    ExpressionTestCase(
        "object_diff_values",
        doc={"a": [{"a": 1}], "b": [{"a": 2}]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for objects with different values",
    ),
    ExpressionTestCase(
        "object_extra_keys",
        doc={"a": [{"a": 1}], "b": [{"a": 1, "b": 2}]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when objects have extra keys",
    ),
    ExpressionTestCase(
        "object_key_order",
        doc={"a": [{"a": 1, "b": 2}], "b": [{"b": 2, "a": 1}]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for objects with different key order",
    ),
]

# Property [Numeric Equivalence]: numeric values equal across int, long, double,
# and decimal128 match, keeping the first operand's type.
SETINTERSECTION_NUMERIC_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_long",
        doc={"a": [1], "b": [Int64(1)]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1],
        msg="$setIntersection should match int and long equivalence keeping int",
    ),
    ExpressionTestCase(
        "int_double",
        doc={"a": [1], "b": [1.0]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1],
        msg="$setIntersection should match int and double equivalence keeping int",
    ),
    ExpressionTestCase(
        "int_decimal128",
        doc={"a": [1], "b": [Decimal128("1")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1],
        msg="$setIntersection should match int and decimal128 equivalence keeping int",
    ),
    ExpressionTestCase(
        "long_double",
        doc={"a": [Int64(1)], "b": [1.0]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Int64(1)],
        msg="$setIntersection should match long and double equivalence keeping long",
    ),
    ExpressionTestCase(
        "long_decimal128",
        doc={"a": [Int64(1)], "b": [Decimal128("1")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Int64(1)],
        msg="$setIntersection should match long and decimal128 equivalence keeping long",
    ),
    ExpressionTestCase(
        "double_decimal128",
        doc={"a": [1.0], "b": [Decimal128("1")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1.0],
        msg="$setIntersection should match double and decimal128 equivalence keeping double",
    ),
    ExpressionTestCase(
        "cross_type_decimal_int",
        doc={"a": [DECIMAL128_TRAILING_ZERO], "b": [1]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DECIMAL128_TRAILING_ZERO],
        msg="$setIntersection should match decimal128 and int equivalence keeping decimal128",
    ),
    ExpressionTestCase(
        "zero_int_long",
        doc={"a": [0], "b": [INT64_ZERO]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[0],
        msg="$setIntersection should match zero int and long equivalence",
    ),
    ExpressionTestCase(
        "zero_int_double",
        doc={"a": [0], "b": [DOUBLE_ZERO]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[0],
        msg="$setIntersection should match zero int and double equivalence",
    ),
    ExpressionTestCase(
        "zero_int_decimal128",
        doc={"a": [0], "b": [DECIMAL128_ZERO]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[0],
        msg="$setIntersection should match zero int and decimal128 equivalence",
    ),
    ExpressionTestCase(
        "all_numeric_types_dedup",
        doc={"a": [1, 1.0, Int64(1)], "b": [Decimal128("1")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1],
        msg="$setIntersection should collapse all numeric types to a single element",
    ),
]

# Property [BSON Type Distinction]: values of different BSON types never match,
# even when Python treats them as equal.
SETINTERSECTION_BSON_DISTINCTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_vs_zero",
        doc={"a": [False], "b": [0]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for false versus zero as different BSON types",
    ),
    ExpressionTestCase(
        "true_vs_one",
        doc={"a": [True], "b": [1]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for true versus one as different BSON types",
    ),
    ExpressionTestCase(
        "false_and_zero_both",
        doc={"a": [False, 0], "b": [False, 0]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[False, 0],
        msg="$setIntersection should return both false and zero when both are present",
    ),
    ExpressionTestCase(
        "bool_vs_numeric",
        doc={"a": [True, False], "b": [1, 2, 4]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for boolean versus numeric comparison",
    ),
    ExpressionTestCase(
        "empty_string_vs_null",
        doc={"a": ["", None], "b": [""]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[""],
        msg="$setIntersection should match empty string while excluding null",
    ),
    ExpressionTestCase(
        "empty_string_vs_null_2",
        doc={"a": ["", None], "b": [None]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[None],
        msg="$setIntersection should match null while excluding empty string",
    ),
]

# Property [NaN Handling]: NaN matches NaN in set context, including across the
# double and decimal128 types.
SETINTERSECTION_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan",
        doc={"a": [FLOAT_NAN, 1], "b": [FLOAT_NAN, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True)],
        msg="$setIntersection should match float NaN in set context",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        doc={"a": [DECIMAL128_NAN, 1], "b": [DECIMAL128_NAN, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DECIMAL128_NAN],
        msg="$setIntersection should match decimal128 NaN in set context",
    ),
    ExpressionTestCase(
        "cross_type_nan",
        doc={"a": [FLOAT_NAN], "b": [DECIMAL128_NAN]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True)],
        msg="$setIntersection should match NaN across double and decimal128, keeping double",
    ),
    ExpressionTestCase(
        "nan_dedup_single_array",
        doc={"a": [FLOAT_NAN, FLOAT_NAN, 1]},
        expression={"$setIntersection": ["$a"]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True), 1],
        msg="$setIntersection should deduplicate NaN within a single array",
    ),
]

# Property [Infinity Handling]: infinities match, including across the double and
# decimal128 types.
SETINTERSECTION_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_inf",
        doc={"a": [FLOAT_INFINITY, 1], "b": [FLOAT_INFINITY, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[FLOAT_INFINITY],
        msg="$setIntersection should match positive infinity",
    ),
    ExpressionTestCase(
        "float_neg_inf",
        doc={"a": [FLOAT_NEGATIVE_INFINITY, 1], "b": [FLOAT_NEGATIVE_INFINITY, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[FLOAT_NEGATIVE_INFINITY],
        msg="$setIntersection should match negative infinity",
    ),
    ExpressionTestCase(
        "cross_type_inf",
        doc={"a": [DECIMAL128_INFINITY], "b": [FLOAT_INFINITY]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DECIMAL128_INFINITY],
        msg="$setIntersection should match infinity across decimal128 and double",
    ),
    ExpressionTestCase(
        "cross_type_neg_inf",
        doc={"a": [DECIMAL128_NEGATIVE_INFINITY], "b": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DECIMAL128_NEGATIVE_INFINITY],
        msg="$setIntersection should match negative infinity across decimal128 and double",
    ),
]

# Property [Negative Zero]: negative zero equals positive zero, including across
# the double and decimal128 types.
SETINTERSECTION_NEG_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_neg_zero_vs_zero",
        doc={"a": [DOUBLE_NEGATIVE_ZERO, 1], "b": [DOUBLE_ZERO, 1]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DOUBLE_NEGATIVE_ZERO, 1],
        msg="$setIntersection should treat double negative zero and zero as equivalent",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero_vs_zero",
        doc={"a": [DECIMAL128_NEGATIVE_ZERO], "b": [DECIMAL128_ZERO]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DECIMAL128_NEGATIVE_ZERO],
        msg="$setIntersection should treat decimal128 negative zero and zero as equivalent",
    ),
    ExpressionTestCase(
        "cross_type_neg_zero",
        doc={"a": [DOUBLE_NEGATIVE_ZERO], "b": [DECIMAL128_ZERO]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DOUBLE_NEGATIVE_ZERO],
        msg="$setIntersection should match negative zero across double and decimal128",
    ),
]

# Property [Decimal128 Representation]: decimal128 values equal in magnitude
# match regardless of trailing zeros or exponent notation.
SETINTERSECTION_DECIMAL128_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "trailing_zeros",
        doc={"a": [DECIMAL128_TRAILING_ZERO], "b": [Decimal128("1.00")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[DECIMAL128_TRAILING_ZERO],
        msg="$setIntersection should match decimal128 values differing only by trailing zeros",
    ),
    ExpressionTestCase(
        "exponent_notation",
        doc={"a": [Decimal128("1E+2")], "b": [Decimal128("100")]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Decimal128("1E+2")],
        msg="$setIntersection should match decimal128 values in exponent notation",
    ),
    ExpressionTestCase(
        "high_precision_match",
        doc={
            "a": [Decimal128("1.000000000000000000000000000000001")],
            "b": [Decimal128("1.000000000000000000000000000000001")],
        },
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[Decimal128("1.000000000000000000000000000000001")],
        msg="$setIntersection should match high-precision decimal128 values",
    ),
    ExpressionTestCase(
        "high_precision_mismatch",
        doc={
            "a": [Decimal128("1.000000000000000000000000000000001")],
            "b": [Decimal128("1.000000000000000000000000000000002")],
        },
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for high-precision decimal128 mismatch",
    ),
]

# Property [Mixed Type Arrays]: intersection over arrays holding several BSON
# types returns only the common elements.
SETINTERSECTION_MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_true_from_mixed",
        doc={"a": [True, True], "b": [True, False]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[True],
        msg="$setIntersection should return true from mixed boolean arrays",
    ),
    ExpressionTestCase(
        "mixed_string_null_bool_int",
        doc={"a": ["string", None, True, 1, {}], "b": ["string", None, True, 1, []]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["string", None, True, 1],
        msg="$setIntersection should return common elements across mixed types",
    ),
]

# Property [String Elements]: string comparison is exact and case-sensitive over
# unicode, emoji, empty, and control-character strings.
SETINTERSECTION_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unicode",
        doc={"a": ["café", "naïve"], "b": ["café", "résumé"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["café"],
        msg="$setIntersection should intersect unicode strings",
    ),
    ExpressionTestCase(
        "emoji",
        doc={"a": ["🎉", "🎊"], "b": ["🎉", "🎈"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["🎉"],
        msg="$setIntersection should intersect emoji strings",
    ),
    ExpressionTestCase(
        "empty_string",
        doc={"a": ["", "a"], "b": ["", "b"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[""],
        msg="$setIntersection should intersect the empty string element",
    ),
    ExpressionTestCase(
        "newline_string",
        doc={"a": ["a\nb", "c"], "b": ["a\nb", "d"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["a\nb"],
        msg="$setIntersection should intersect strings containing a newline",
    ),
    ExpressionTestCase(
        "case_sensitive",
        doc={"a": ["abc", "def"], "b": ["ABC", "def"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["def"],
        msg="$setIntersection should treat strings as case-sensitive",
    ),
]

SETINTERSECTION_TYPE_TESTS: list[ExpressionTestCase] = (
    SETINTERSECTION_ELEMENT_TYPE_TESTS
    + SETINTERSECTION_DISTINCTION_TESTS
    + SETINTERSECTION_NUMERIC_EQUIV_TESTS
    + SETINTERSECTION_BSON_DISTINCTION_TESTS
    + SETINTERSECTION_NAN_TESTS
    + SETINTERSECTION_INFINITY_TESTS
    + SETINTERSECTION_NEG_ZERO_TESTS
    + SETINTERSECTION_DECIMAL128_TESTS
    + SETINTERSECTION_STRING_TESTS
    + SETINTERSECTION_MIXED_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETINTERSECTION_TYPE_TESTS))
def test_setIntersection_types(collection, test):
    """Test $setIntersection element type handling, numeric equivalence, and special values."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg, ignore_order=True)
