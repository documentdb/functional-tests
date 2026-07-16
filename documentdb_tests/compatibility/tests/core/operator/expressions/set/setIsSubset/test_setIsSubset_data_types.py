"""Tests for $setIsSubset element type handling, numeric equivalence, and special values."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    INT32_MAX,
    INT64_ZERO,
)

# Property [Element Type Coverage]: arrays of any single BSON element type
# resolve membership by element value.
SETISSUBSET_ELEMENT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "strings",
        doc={"a": ["a", "b"], "b": ["a", "b", "c"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for string elements",
    ),
    ExpressionTestCase(
        "ints",
        doc={"a": [1, 2, 3], "b": [1, 2, 3, 4]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for int elements",
    ),
    ExpressionTestCase(
        "longs",
        doc={"a": [Int64(1), Int64(2)], "b": [Int64(1), Int64(2), Int64(3)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for long elements",
    ),
    ExpressionTestCase(
        "doubles",
        doc={"a": [1.1, 2.2], "b": [1.1, 2.2, 3.3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for double elements",
    ),
    ExpressionTestCase(
        "decimals",
        doc={
            "a": [Decimal128("1"), Decimal128("2")],
            "b": [Decimal128("1"), Decimal128("2"), Decimal128("3")],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for decimal128 elements",
    ),
    ExpressionTestCase(
        "booleans",
        doc={"a": [True], "b": [True, False]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for boolean elements",
    ),
    ExpressionTestCase(
        "dates",
        doc={
            "a": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            "b": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            ],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for date elements",
    ),
    ExpressionTestCase(
        "nulls",
        doc={"a": [None], "b": [None, 1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for null elements",
    ),
    ExpressionTestCase(
        "objects",
        doc={"a": [{"a": 1}], "b": [{"a": 1}, {"b": 2}]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for object elements",
    ),
    ExpressionTestCase(
        "objectids",
        doc={
            "a": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")],
            "b": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for objectid elements",
    ),
    ExpressionTestCase(
        "regex",
        doc={"a": [Regex("abc", "")], "b": [Regex("abc", ""), Regex("def", "")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for regex elements",
    ),
    ExpressionTestCase(
        "binary",
        doc={
            "a": [Binary(b"\x01\x02\x03", 0)],
            "b": [Binary(b"\x01\x02\x03", 0), Binary(b"\x04\x05\x06", 0)],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for binary elements",
    ),
    ExpressionTestCase(
        "timestamps",
        doc={"a": [Timestamp(1, 1)], "b": [Timestamp(1, 1), Timestamp(2, 2)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for timestamp elements",
    ),
    ExpressionTestCase(
        "minkey",
        doc={"a": [MinKey()], "b": [MinKey(), 1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for minkey elements",
    ),
    ExpressionTestCase(
        "maxkey",
        doc={"a": [MaxKey()], "b": [MaxKey(), 1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for maxkey elements",
    ),
    ExpressionTestCase(
        "nested_arrays",
        doc={"a": [["x", "y"]], "b": [["x", "y"], ["z"]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should resolve membership for nested array elements",
    ),
]

# Property [Mixed Types]: an operand may hold elements of different BSON types
# and membership is resolved per element.
SETISSUBSET_MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_subset",
        doc={"a": [1, "a", True], "b": [1, "a", True, None]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a mixed-type subset",
    ),
    ExpressionTestCase(
        "mixed_not_subset",
        doc={"a": [1, "a", True, None], "b": [1, "a", True]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a mixed-type non-subset",
    ),
    ExpressionTestCase(
        "mixed_with_null_bool_obj",
        doc={"a": ["string", None, 2], "b": ["string", None, 2, False, {}]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a mix with null, bool, and object",
    ),
    ExpressionTestCase(
        "int_vs_string_no_overlap",
        doc={"a": [1, 2, 3], "b": ["x", "y", "z"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for different types with no overlap",
    ),
    ExpressionTestCase(
        "object_and_numeric",
        doc={"a": [{"a": 2}, Int64(1)], "b": [1, {"a": 2}, 1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for an object and cross-type numeric mix",
    ),
    ExpressionTestCase(
        "bool_null_timestamp",
        doc={"a": [True, False, None], "b": [None, False, True, Timestamp(1980, 0)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a bool, null, and timestamp mix",
    ),
    ExpressionTestCase(
        "all_numeric_types",
        doc={"a": [1.0, Int64(2), 3], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true when all numeric types are treated as equivalent",
    ),
]

# Property [Numeric Equivalence]: numeric elements compare by value across int,
# long, double, and decimal128 types.
SETISSUBSET_NUMERIC_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_long",
        doc={"a": [1], "b": [Int64(1)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat an int as equal to a long",
    ),
    ExpressionTestCase(
        "int_double",
        doc={"a": [1], "b": [1.0]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat an int as equal to a double",
    ),
    ExpressionTestCase(
        "int_decimal",
        doc={"a": [1], "b": [Decimal128("1")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat an int as equal to a decimal128",
    ),
    ExpressionTestCase(
        "long_double",
        doc={"a": [Int64(1)], "b": [1.0]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat a long as equal to a double",
    ),
    ExpressionTestCase(
        "long_decimal",
        doc={"a": [Int64(1)], "b": [Decimal128("1")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat a long as equal to a decimal128",
    ),
    ExpressionTestCase(
        "double_decimal",
        doc={"a": [1.0], "b": [Decimal128("1")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat a double as equal to a decimal128",
    ),
    ExpressionTestCase(
        "all_four_types",
        doc={
            "a": [1, Int64(2), 3.0, Decimal128("4")],
            "b": [Decimal128("1"), 2.0, Int64(3), 4],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should cross-match across all four numeric types",
    ),
    ExpressionTestCase(
        "zero_equiv",
        doc={"a": [0], "b": [INT64_ZERO]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat int zero as equal to long zero",
    ),
    ExpressionTestCase(
        "int_vs_double_not_equal",
        doc={"a": [1], "b": [1.1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for an int not equal to a fractional double",
    ),
    ExpressionTestCase(
        "int32_max_cross",
        doc={"a": [INT32_MAX], "b": [Int64(INT32_MAX)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat int32 max as equal to the long of the same value",
    ),
    ExpressionTestCase(
        "cross_type_nested",
        doc={"a": [["a", Decimal128("2"), Decimal128("4"), 6]], "b": [["a", 2, 4, 6]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should cross-match numeric types inside a nested array element",
    ),
]

# Property [Type Distinction]: elements of distinct BSON types are not equal even
# when they look similar.
SETISSUBSET_BSON_DISTINCTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_vs_zero",
        doc={"a": [False], "b": [0]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for false versus int zero",
    ),
    ExpressionTestCase(
        "true_vs_one",
        doc={"a": [True], "b": [1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for true versus int one",
    ),
    ExpressionTestCase(
        "empty_string_vs_null",
        doc={"a": [""], "b": [None]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for an empty string versus null",
    ),
    ExpressionTestCase(
        "date_vs_numeric",
        doc={"a": [datetime(1970, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)], "b": [1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a date versus its epoch-millis numeric value",
    ),
]

# Property [NaN Handling]: NaN is equal to NaN in set-membership context and is
# distinct from ordinary numbers, across double and decimal128.
SETISSUBSET_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_both",
        doc={"a": [FLOAT_NAN], "b": [FLOAT_NAN]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat NaN as equal to NaN in set context",
    ),
    ExpressionTestCase(
        "decimal_nan_vs_float_nan",
        doc={"a": [DECIMAL128_NAN], "b": [FLOAT_NAN]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 NaN as equal to double NaN",
    ),
    ExpressionTestCase(
        "float_nan_vs_decimal_nan",
        doc={"a": [FLOAT_NAN], "b": [DECIMAL128_NAN]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat double NaN as equal to decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_not_in_numbers",
        doc={"a": [FLOAT_NAN], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for NaN not present in a number array",
    ),
    ExpressionTestCase(
        "nan_with_other_specials",
        doc={
            "a": [None, DECIMAL128_NAN],
            "b": [None, FLOAT_NAN, FLOAT_INFINITY, MinKey(), MaxKey()],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should cross-match NaN inside a mixed special-value array",
    ),
]

# Property [Infinity Handling]: infinities compare by value and sign across double
# and decimal128.
SETISSUBSET_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_subset",
        doc={"a": [FLOAT_INFINITY], "b": [FLOAT_INFINITY, 1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for infinity present in the superset",
    ),
    ExpressionTestCase(
        "neg_inf_subset",
        doc={"a": [FLOAT_NEGATIVE_INFINITY], "b": [FLOAT_NEGATIVE_INFINITY, 1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for negative infinity present in the superset",
    ),
    ExpressionTestCase(
        "decimal_inf_vs_float_inf",
        doc={"a": [DECIMAL128_INFINITY], "b": [FLOAT_INFINITY]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 infinity as equal to double infinity",
    ),
    ExpressionTestCase(
        "decimal_neg_inf_vs_float_neg_inf",
        doc={"a": [DECIMAL128_NEGATIVE_INFINITY], "b": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 negative infinity as double negative infinity",
    ),
    ExpressionTestCase(
        "inf_not_neg_inf",
        doc={"a": [FLOAT_INFINITY], "b": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for infinity not equal to negative infinity",
    ),
    ExpressionTestCase(
        "float_inf_cross_decimal",
        doc={
            "a": [None, FLOAT_NAN, FLOAT_INFINITY],
            "b": [None, DECIMAL128_NAN, DECIMAL128_INFINITY, MinKey(), MaxKey()],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should cross-match infinity and NaN across types",
    ),
]

# Property [Negative Zero]: negative zero equals positive zero across double,
# decimal128, and int.
SETISSUBSET_NEG_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_neg_zero_vs_zero",
        doc={"a": [DOUBLE_NEGATIVE_ZERO], "b": [DOUBLE_ZERO]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat double negative zero as equal to double zero",
    ),
    ExpressionTestCase(
        "double_neg_zero_vs_int_zero",
        doc={"a": [DOUBLE_NEGATIVE_ZERO], "b": [0]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat double negative zero as equal to int zero",
    ),
    ExpressionTestCase(
        "decimal_neg_zero_vs_zero",
        doc={"a": [DECIMAL128_NEGATIVE_ZERO], "b": [DECIMAL128_ZERO]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 negative zero as equal to decimal128 zero",
    ),
    ExpressionTestCase(
        "decimal_neg_zero_vs_int_zero",
        doc={"a": [DECIMAL128_NEGATIVE_ZERO], "b": [0]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 negative zero as equal to int zero",
    ),
]

# Property [Object Elements]: object elements compare by exact field order and
# value, without descending for set semantics.
SETISSUBSET_OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_diff_field_order",
        doc={"a": [{"a": 1, "b": 2}], "b": [{"b": 2, "a": 1}]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false when object field order differs",
    ),
    ExpressionTestCase(
        "obj_extra_fields",
        doc={"a": [{"a": 1}], "b": [{"a": 1, "b": 2}]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for an object with extra fields",
    ),
    ExpressionTestCase(
        "nested_obj",
        doc={"a": [{"a": {"b": 1}}], "b": [{"a": {"b": 1}}, {"a": {"b": 2}}]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a nested object match",
    ),
    ExpressionTestCase(
        "empty_obj_match",
        doc={"a": [{}], "b": [{}, {"a": 1}]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for an empty object match",
    ),
    ExpressionTestCase(
        "empty_obj_no_match",
        doc={"a": [{}], "b": [{"a": 1}]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for an empty object not in a non-empty set",
    ),
]

# Property [String Elements]: string elements compare exactly, including empty,
# case, unicode, and control characters.
SETISSUBSET_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_string",
        doc={"a": [""], "b": ["", "a"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for an empty-string element",
    ),
    ExpressionTestCase(
        "case_sensitive",
        doc={"a": ["A"], "b": ["a"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a case-sensitive mismatch",
    ),
    ExpressionTestCase(
        "unicode",
        doc={"a": ["café"], "b": ["café", "naïve"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for unicode string elements",
    ),
    ExpressionTestCase(
        "special_chars",
        doc={"a": ["a\nb"], "b": ["a\nb", "c"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for strings with special characters",
    ),
]

# Property [Null Elements]: a null element is an ordinary value subject to set
# membership.
SETISSUBSET_NULL_ELEM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_in_subset",
        doc={"a": [None], "b": [None, 1, 2]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a null element present in the superset",
    ),
    ExpressionTestCase(
        "null_not_in_superset",
        doc={"a": [None], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a null element not in the superset",
    ),
    ExpressionTestCase(
        "null_in_both",
        doc={"a": [None, 1], "b": [None, 1, 2]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a null element present in both arrays",
    ),
    ExpressionTestCase(
        "only_nulls",
        doc={"a": [None, None], "b": [None]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for an array of only nulls after dedup",
    ),
]

# Property [Boolean Elements]: boolean membership respects subset direction.
SETISSUBSET_BOOL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_not_subset",
        doc={"a": [True, False], "b": [True]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a boolean non-subset",
    ),
]

# Property [Regex Elements]: regex elements compare by both pattern and flags.
SETISSUBSET_REGEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_regex",
        doc={"a": [Regex("^abc", "i")], "b": [Regex("^abc", "i"), Regex("def", "")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a matching regex element",
    ),
    ExpressionTestCase(
        "diff_flags",
        doc={"a": [Regex("abc", "")], "b": [Regex("abc", "i")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for different regex flags",
    ),
    ExpressionTestCase(
        "diff_pattern",
        doc={"a": [Regex("abc", "")], "b": [Regex("def", "")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for different regex patterns",
    ),
]

# Property [BinData Elements]: binary elements compare by both bytes and subtype.
SETISSUBSET_BINDATA_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "diff_bindata",
        doc={"a": [Binary(b"\x01\x02\x03", 0)], "b": [Binary(b"\x04\x05\x06", 0)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for different binary data",
    ),
    ExpressionTestCase(
        "diff_subtype",
        doc={"a": [Binary(b"\x01\x02\x03", 0)], "b": [Binary(b"\x01\x02\x03", 4)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for the same bytes with a different subtype",
    ),
]

# Property [Date And Timestamp Elements]: dates and timestamps compare by their
# full value.
SETISSUBSET_DATE_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_date",
        doc={
            "a": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            "b": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a matching date",
    ),
    ExpressionTestCase(
        "diff_date",
        doc={
            "a": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            "b": [datetime(2024, 1, 2, tzinfo=timezone.utc)],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for different dates",
    ),
    ExpressionTestCase(
        "same_timestamp",
        doc={"a": [Timestamp(1000, 1)], "b": [Timestamp(1000, 1), Timestamp(2000, 1)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a matching timestamp",
    ),
    ExpressionTestCase(
        "diff_timestamp",
        doc={"a": [Timestamp(1000, 1)], "b": [Timestamp(1000, 2)]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for different timestamps",
    ),
]

# Property [MinKey And MaxKey Elements]: the boundary keys compare as their own
# distinct values.
SETISSUBSET_MINMAX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minkey_not_maxkey",
        doc={"a": [MinKey()], "b": [MaxKey()]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for minkey not equal to maxkey",
    ),
]

# Property [ObjectId Elements]: objectid elements compare by their full value.
SETISSUBSET_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "diff_oid",
        doc={
            "a": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")],
            "b": [ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for different objectids",
    ),
]

# Property [Decimal128 Precision]: decimal128 elements compare by value with
# trailing-zero and exponent normalization.
SETISSUBSET_DECIMAL_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_vs_int",
        doc={"a": [Decimal128("1")], "b": [1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 one as equal to int one",
    ),
    ExpressionTestCase(
        "trailing_zeros",
        doc={"a": [DECIMAL128_TRAILING_ZERO], "b": [Decimal128("1.00")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 trailing zeros as equivalent",
    ),
    ExpressionTestCase(
        "exponent_notation",
        doc={"a": [Decimal128("1E+2")], "b": [Decimal128("100")]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should treat decimal128 exponent notation as equivalent",
    ),
    ExpressionTestCase(
        "high_precision_match",
        doc={
            "a": [Decimal128("1.000000000000000000000000000000001")],
            "b": [Decimal128("1.000000000000000000000000000000001")],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a high-precision decimal128 match",
    ),
    ExpressionTestCase(
        "high_precision_mismatch",
        doc={
            "a": [Decimal128("1.000000000000000000000000000000001")],
            "b": [Decimal128("1.000000000000000000000000000000002")],
        },
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a high-precision decimal128 mismatch",
    ),
]

SETISSUBSET_TYPE_TESTS: list[ExpressionTestCase] = (
    SETISSUBSET_ELEMENT_TYPE_TESTS
    + SETISSUBSET_MIXED_TYPE_TESTS
    + SETISSUBSET_NUMERIC_EQUIV_TESTS
    + SETISSUBSET_BSON_DISTINCTION_TESTS
    + SETISSUBSET_NAN_TESTS
    + SETISSUBSET_INFINITY_TESTS
    + SETISSUBSET_NEG_ZERO_TESTS
    + SETISSUBSET_OBJECT_TESTS
    + SETISSUBSET_STRING_TESTS
    + SETISSUBSET_NULL_ELEM_TESTS
    + SETISSUBSET_BOOL_TESTS
    + SETISSUBSET_REGEX_TESTS
    + SETISSUBSET_BINDATA_TESTS
    + SETISSUBSET_DATE_TIMESTAMP_TESTS
    + SETISSUBSET_MINMAX_TESTS
    + SETISSUBSET_OBJECTID_TESTS
    + SETISSUBSET_DECIMAL_PRECISION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETISSUBSET_TYPE_TESTS))
def test_setIsSubset_types(collection, test):
    """Test $setIsSubset element type handling, numeric equivalence, and special values."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
