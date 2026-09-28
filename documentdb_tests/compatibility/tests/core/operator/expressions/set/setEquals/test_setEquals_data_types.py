"""Tests for $setEquals element type handling, numeric equivalence, and special values."""

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
# compare equal when they hold the same elements.
SETEQUALS_ELEMENT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "integers",
        doc={"a": [4, 5, 6], "b": [6, 5, 4]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare integer arrays",
    ),
    ExpressionTestCase(
        "longs",
        doc={"a": [Int64(1), Int64(2)], "b": [Int64(2), Int64(1)]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare long arrays",
    ),
    ExpressionTestCase(
        "doubles",
        doc={"a": [1.5, 2.5], "b": [2.5, 1.5]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare double arrays",
    ),
    ExpressionTestCase(
        "decimal128",
        doc={"a": [Decimal128("1"), Decimal128("2")], "b": [Decimal128("2"), Decimal128("1")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare decimal128 arrays",
    ),
    ExpressionTestCase(
        "strings",
        doc={"a": ["a", "b"], "b": ["b", "a"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare string arrays",
    ),
    ExpressionTestCase(
        "booleans",
        doc={"a": [True, False], "b": [False, True]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare boolean arrays",
    ),
    ExpressionTestCase(
        "dates",
        doc={
            "a": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            ],
            "b": [
                datetime(2024, 1, 2, tzinfo=timezone.utc),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
            ],
        },
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare date arrays",
    ),
    ExpressionTestCase(
        "null_elem",
        doc={"a": [None, 7], "b": [7, None]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare null-element arrays",
    ),
    ExpressionTestCase(
        "objectid",
        doc={
            "a": [ObjectId("507f1f77bcf86cd799439011")],
            "b": [ObjectId("507f1f77bcf86cd799439011")],
        },
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare ObjectId arrays",
    ),
    ExpressionTestCase(
        "objects",
        doc={"a": [{"a": 1}], "b": [{"a": 1}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare object arrays",
    ),
    ExpressionTestCase(
        "nested_arrays",
        doc={"a": [["x", "y"]], "b": [["x", "y"]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare nested-array arrays",
    ),
    ExpressionTestCase(
        "regex",
        doc={"a": [Regex("abc", "")], "b": [Regex("abc", "")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare regex arrays",
    ),
    ExpressionTestCase(
        "javascript",
        doc={"a": [Code("function(){}")], "b": [Code("function(){}")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare javascript code arrays",
    ),
    ExpressionTestCase(
        "binary",
        doc={"a": [Binary(b"\x01", 0)], "b": [Binary(b"\x01", 0)]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare binary arrays",
    ),
    ExpressionTestCase(
        "timestamp",
        doc={"a": [Timestamp(1, 1)], "b": [Timestamp(1, 1)]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare timestamp arrays",
    ),
    ExpressionTestCase(
        "minkey",
        doc={"a": [MinKey()], "b": [MinKey()]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare MinKey arrays",
    ),
    ExpressionTestCase(
        "maxkey",
        doc={"a": [MaxKey()], "b": [MaxKey()]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare MaxKey arrays",
    ),
]

# Property [Numeric Equivalence]: numeric values equal across int, long, double,
# and decimal128 are treated as the same element.
SETEQUALS_NUMERIC_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_long",
        doc={"a": [1], "b": [Int64(1)]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat int and long as equivalent",
    ),
    ExpressionTestCase(
        "int_double",
        doc={"a": [1], "b": [1.0]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat int and double as equivalent",
    ),
    ExpressionTestCase(
        "int_decimal",
        doc={"a": [1], "b": [Decimal128("1")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat int and decimal128 as equivalent",
    ),
    ExpressionTestCase(
        "long_double",
        doc={"a": [Int64(1)], "b": [1.0]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat long and double as equivalent",
    ),
    ExpressionTestCase(
        "long_decimal",
        doc={"a": [Int64(1)], "b": [Decimal128("1")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat long and decimal128 as equivalent",
    ),
    ExpressionTestCase(
        "double_decimal",
        doc={"a": [1.0], "b": [Decimal128("1")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat double and decimal128 as equivalent",
    ),
    ExpressionTestCase(
        "zero_int_long",
        doc={"a": [0], "b": [INT64_ZERO]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat zero int and long as equivalent",
    ),
    ExpressionTestCase(
        "zero_int_double",
        doc={"a": [0], "b": [DOUBLE_ZERO]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat zero int and double as equivalent",
    ),
    ExpressionTestCase(
        "zero_int_decimal",
        doc={"a": [0], "b": [DECIMAL128_ZERO]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat zero int and decimal128 as equivalent",
    ),
    ExpressionTestCase(
        "dedup_cross_type",
        doc={"a": [1, 1, 1], "b": [Int64(1)]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should deduplicate with cross-type equivalence",
    ),
    ExpressionTestCase(
        "all_ones",
        doc={"a": [1, Int64(1), 1.0], "b": [Decimal128("1")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat all numeric ones as equivalent",
    ),
    ExpressionTestCase(
        "mixed_numeric",
        doc={"a": [1, Int64(2), 3.0], "b": [Decimal128("3"), 2, Int64(1)]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat mixed numeric types as equivalent",
    ),
    ExpressionTestCase(
        "all_ones_dedup",
        doc={"a": [1, Int64(1), 1.0, Decimal128("1")], "b": [1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should collapse all numeric ones to a single element",
    ),
    ExpressionTestCase(
        "decimal128_equiv",
        doc={
            "a": [Decimal128("1e0"), Decimal128("2")],
            "b": [Decimal128("1.00"), Decimal128("200E-2")],
        },
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat equivalent decimal128 representations as equal",
    ),
]

# Property [Negative Zero]: negative zero equals positive zero, including across
# the double and decimal128 types.
SETEQUALS_NEG_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_neg_zero",
        doc={"a": [DOUBLE_ZERO], "b": [DOUBLE_NEGATIVE_ZERO]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat double zero and negative zero as equivalent",
    ),
    ExpressionTestCase(
        "decimal_neg_zero",
        doc={"a": [DECIMAL128_ZERO], "b": [DECIMAL128_NEGATIVE_ZERO]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat decimal128 zero and negative zero as equivalent",
    ),
    ExpressionTestCase(
        "neg_zero_with_other",
        doc={"a": [DOUBLE_NEGATIVE_ZERO, 1], "b": [DOUBLE_ZERO, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat negative zero as equivalent alongside other elements",
    ),
]

# Property [BSON Type Distinction]: values of different BSON types never match,
# even when they appear equivalent in some languages.
SETEQUALS_BSON_DISTINCTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_vs_zero",
        doc={"a": [False], "b": [0]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for false versus zero as different BSON types",
    ),
    ExpressionTestCase(
        "true_vs_one",
        doc={"a": [True], "b": [1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for true versus one as different BSON types",
    ),
    ExpressionTestCase(
        "false_zero_both",
        doc={"a": [False, 0], "b": [0, False]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when both operands contain false and zero",
    ),
    ExpressionTestCase(
        "empty_str_vs_null",
        doc={"a": [""], "b": [None]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for empty string versus null",
    ),
    ExpressionTestCase(
        "bool_vs_numeric_mixed",
        doc={"a": [True, False], "b": [1, 0]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for booleans versus numerics",
    ),
    ExpressionTestCase(
        "obj_vs_array",
        doc={"a": [{}], "b": [[]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for an empty object versus an empty array",
    ),
]

# Property [NaN Handling]: NaN matches NaN in set context, including across the
# double and decimal128 types.
SETEQUALS_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_both",
        doc={"a": [FLOAT_NAN], "b": [FLOAT_NAN]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat NaN as equal to NaN in set context",
    ),
    ExpressionTestCase(
        "nan_with_int",
        doc={"a": [FLOAT_NAN, 1], "b": [1, FLOAT_NAN]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat NaN as equal alongside an int element",
    ),
    ExpressionTestCase(
        "nan_cross_type",
        doc={"a": [DECIMAL128_NAN], "b": [FLOAT_NAN]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should match NaN across decimal128 and double",
    ),
    ExpressionTestCase(
        "nan_dedup",
        doc={"a": [FLOAT_NAN, FLOAT_NAN, 1], "b": [FLOAT_NAN, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should deduplicate NaN elements",
    ),
]

# Property [Infinity Handling]: infinities match, including across the double and
# decimal128 types.
SETEQUALS_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_both",
        doc={"a": [FLOAT_INFINITY], "b": [FLOAT_INFINITY]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat positive infinity as equal to positive infinity",
    ),
    ExpressionTestCase(
        "neg_inf_both",
        doc={"a": [FLOAT_NEGATIVE_INFINITY], "b": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should treat negative infinity as equal to negative infinity",
    ),
    ExpressionTestCase(
        "inf_vs_neg_inf",
        doc={"a": [FLOAT_INFINITY], "b": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for positive infinity versus negative infinity",
    ),
    ExpressionTestCase(
        "inf_cross_type",
        doc={"a": [DECIMAL128_INFINITY], "b": [FLOAT_INFINITY]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should match infinity across decimal128 and double",
    ),
    ExpressionTestCase(
        "neg_inf_cross_type",
        doc={"a": [DECIMAL128_NEGATIVE_INFINITY], "b": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should match negative infinity across decimal128 and double",
    ),
]

# Property [Object Elements]: objects match only when their keys, values, and key
# order are identical.
SETEQUALS_OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_obj",
        doc={"a": [{"a": 1, "b": 2}], "b": [{"a": 1, "b": 2}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for the same object",
    ),
    ExpressionTestCase(
        "diff_key_order",
        doc={"a": [{"a": 1, "b": 2}], "b": [{"b": 2, "a": 1}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for different key order",
    ),
    ExpressionTestCase(
        "diff_values",
        doc={"a": [{"a": 1}], "b": [{"a": 2}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for different object values",
    ),
    ExpressionTestCase(
        "extra_keys",
        doc={"a": [{"a": 1}], "b": [{"a": 1, "b": 2}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for extra object keys",
    ),
    ExpressionTestCase(
        "nested_obj",
        doc={"a": [{"a": {"b": 1}}], "b": [{"a": {"b": 1}}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for nested objects",
    ),
    ExpressionTestCase(
        "empty_obj",
        doc={"a": [{}], "b": [{}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for empty objects",
    ),
    ExpressionTestCase(
        "empty_vs_nonempty",
        doc={"a": [{}], "b": [{"a": 1}]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for an empty versus a non-empty object",
    ),
]

# Property [String Elements]: string comparison is exact, case-sensitive, and
# unicode-aware.
SETEQUALS_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unicode",
        doc={"a": ["café", "naïve"], "b": ["naïve", "café"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare unicode strings",
    ),
    ExpressionTestCase(
        "empty_str",
        doc={"a": ["", 9], "b": [9, ""]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should compare empty strings",
    ),
    ExpressionTestCase(
        "case_sensitive",
        doc={"a": ["abc"], "b": ["ABC"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should treat strings as case-sensitive",
    ),
]

# Property [Mixed Type Arrays]: equality over arrays holding several BSON types
# holds only when every distinct element matches.
SETEQUALS_MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_equal",
        doc={"a": [2, "x", False], "b": ["x", False, 2]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for mixed types with the same elements",
    ),
    ExpressionTestCase(
        "mixed_not_equal",
        doc={"a": [2, "x", False], "b": ["x", False, 3]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for mixed types with a different element",
    ),
    ExpressionTestCase(
        "null_int_str",
        doc={"a": [None, 1, "a"], "b": [1, "a", None]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for null with int and string elements",
    ),
    ExpressionTestCase(
        "mixed_str_none_bool_int",
        doc={"a": ["string", None, True, 1], "b": ["string", None, True, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for identical mixed-type arrays",
    ),
    ExpressionTestCase(
        "obj_vs_array_in_mixed",
        doc={"a": ["string", None, True, 1, {}], "b": ["string", None, True, 1, []]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for an object versus an array within mixed types",
    ),
]

# Property [Special Values Combined]: null, NaN, infinity, MinKey, and MaxKey
# match as elements regardless of order.
SETEQUALS_SPECIAL_COMBINED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "special_all",
        doc={
            "a": [None, FLOAT_NAN, FLOAT_INFINITY, MinKey(), MaxKey()],
            "b": [MaxKey(), None, FLOAT_INFINITY, FLOAT_NAN, MinKey()],
        },
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for the same set of special values",
    ),
]

# Property [Decimal128 Representation]: decimal128 values equal in magnitude match
# regardless of trailing zeros or exponent notation.
SETEQUALS_DECIMAL128_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_trailing_zeros",
        doc={"a": [DECIMAL128_TRAILING_ZERO], "b": [Decimal128("1.00")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should match decimal128 values differing only by trailing zeros",
    ),
    ExpressionTestCase(
        "decimal_exponent_notation",
        doc={"a": [Decimal128("1E+2")], "b": [Decimal128("100")]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should match decimal128 values in exponent notation",
    ),
    ExpressionTestCase(
        "decimal_high_precision_match",
        doc={
            "a": [Decimal128("1.000000000000000000000000000000001")],
            "b": [Decimal128("1.000000000000000000000000000000001")],
        },
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should match high-precision decimal128 values",
    ),
    ExpressionTestCase(
        "decimal_high_precision_mismatch",
        doc={
            "a": [Decimal128("1.000000000000000000000000000000001")],
            "b": [Decimal128("1.000000000000000000000000000000002")],
        },
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for a high-precision decimal128 mismatch",
    ),
]

SETEQUALS_TYPE_TESTS: list[ExpressionTestCase] = (
    SETEQUALS_ELEMENT_TYPE_TESTS
    + SETEQUALS_NUMERIC_EQUIV_TESTS
    + SETEQUALS_NEG_ZERO_TESTS
    + SETEQUALS_BSON_DISTINCTION_TESTS
    + SETEQUALS_NAN_TESTS
    + SETEQUALS_INFINITY_TESTS
    + SETEQUALS_OBJECT_TESTS
    + SETEQUALS_STRING_TESTS
    + SETEQUALS_MIXED_TYPE_TESTS
    + SETEQUALS_SPECIAL_COMBINED_TESTS
    + SETEQUALS_DECIMAL128_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETEQUALS_TYPE_TESTS))
def test_setEquals_types(collection, test):
    """Test $setEquals element type handling, numeric equivalence, and special values."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
