"""Tests for $setDifference type distinction, numeric equivalence, and BSON element types."""

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

# Property [BSON Type Distinction]: values of different BSON types are never equal
# even when they look similar.
SETDIFFERENCE_BSON_DISTINCTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_vs_0",
        doc={"arr1": [False, 0], "arr2": [False]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[0],
        msg="Should treat false and zero as distinct BSON types",
    ),
    ExpressionTestCase(
        "true_vs_1",
        doc={"arr1": [True, 1], "arr2": [True]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat true and one as distinct BSON types",
    ),
    ExpressionTestCase(
        "null_in_array",
        doc={"arr1": [None, 1], "arr2": [1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[None],
        msg="Should preserve null element when it is not in the second array",
    ),
    ExpressionTestCase(
        "empty_string_vs_null",
        doc={"arr1": ["", None], "arr2": [None]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[""],
        msg="Should treat empty string and null as distinct BSON types",
    ),
]

# Property [NaN Handling]: NaN is equal to NaN across float and decimal128 in the
# set comparison context, and is deduplicated.
SETDIFFERENCE_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_in_second",
        doc={"arr1": [1, 2], "arr2": [FLOAT_NAN, 1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[2],
        msg="Should handle NaN in second array and remove matching elements",
    ),
    ExpressionTestCase(
        "nan_in_both",
        doc={"arr1": [FLOAT_NAN, 1], "arr2": [FLOAT_NAN, 2]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat NaN as equal to NaN in set comparison context",
    ),
    ExpressionTestCase(
        "nan_cross_type",
        doc={"arr1": [FLOAT_NAN, 1], "arr2": [DECIMAL128_NAN, 2]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat float NaN as equal to decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_preserved_in_first",
        doc={"arr1": [FLOAT_NAN, 1, 2], "arr2": [1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True), 2],
        msg="Should preserve NaN element in result when not removed by second array",
    ),
    ExpressionTestCase(
        "nan_dedup",
        doc={"arr1": [FLOAT_NAN, FLOAT_NAN, 1], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True), 1],
        msg="Should deduplicate multiple NaN elements to a single NaN",
    ),
]

# Property [Infinity Handling]: positive and negative infinity are distinct, and
# match across float and decimal128.
SETDIFFERENCE_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_in_first",
        doc={"arr1": [FLOAT_INFINITY, 1], "arr2": [1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[FLOAT_INFINITY],
        msg="Should preserve infinity when it is not in the second array",
    ),
    ExpressionTestCase(
        "neg_inf_in_first",
        doc={"arr1": [FLOAT_NEGATIVE_INFINITY, 1], "arr2": [1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[FLOAT_NEGATIVE_INFINITY],
        msg="Should preserve negative infinity when it is not in the second array",
    ),
    ExpressionTestCase(
        "inf_removed",
        doc={"arr1": [FLOAT_INFINITY, 1], "arr2": [FLOAT_INFINITY]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should remove infinity when it appears in the second array",
    ),
    ExpressionTestCase(
        "inf_vs_neg_inf",
        doc={"arr1": [FLOAT_INFINITY], "arr2": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[FLOAT_INFINITY],
        msg="Should treat positive and negative infinity as distinct values",
    ),
    ExpressionTestCase(
        "neg_inf_vs_neg_inf",
        doc={"arr1": [FLOAT_NEGATIVE_INFINITY], "arr2": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when both arrays contain negative infinity",
    ),
    ExpressionTestCase(
        "inf_cross_type",
        doc={"arr1": [DECIMAL128_INFINITY, 1], "arr2": [FLOAT_INFINITY]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat decimal128 Infinity as equal to float Infinity",
    ),
    ExpressionTestCase(
        "neg_inf_cross_type",
        doc={"arr1": [DECIMAL128_NEGATIVE_INFINITY, 1], "arr2": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat decimal128 -Infinity as equal to float -Infinity",
    ),
]

# Property [Numeric Equivalence]: int, long, double, and decimal128 that represent
# the same value are equal for set membership.
SETDIFFERENCE_NUMERIC_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_vs_long",
        doc={"arr1": [1, 2], "arr2": [Int64(1)]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[2],
        msg="Should treat int and long as equivalent for same value",
    ),
    ExpressionTestCase(
        "int_vs_double",
        doc={"arr1": [1, 2], "arr2": [1.0]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[2],
        msg="Should treat int and double as equivalent for same value",
    ),
    ExpressionTestCase(
        "int_vs_decimal",
        doc={"arr1": [1, 2], "arr2": [Decimal128("1")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[2],
        msg="Should treat int and decimal128 as equivalent for same value",
    ),
    ExpressionTestCase(
        "long_vs_double",
        doc={"arr1": [Int64(1), Int64(2)], "arr2": [1.0]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Int64(2)],
        msg="Should treat long and double as equivalent for same value",
    ),
    ExpressionTestCase(
        "long_vs_decimal",
        doc={"arr1": [Int64(1), Int64(2)], "arr2": [Decimal128("1")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Int64(2)],
        msg="Should treat long and decimal128 as equivalent for same value",
    ),
    ExpressionTestCase(
        "double_vs_decimal",
        doc={"arr1": [1.0, 2.0], "arr2": [Decimal128("1")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[2.0],
        msg="Should treat double and decimal128 as equivalent for same value",
    ),
    ExpressionTestCase(
        "all_four_types",
        doc={"arr1": [1, Int64(1), 1.0, Decimal128("1")], "arr2": [1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when all four numeric types represent the same value",
    ),
    ExpressionTestCase(
        "int0_vs_double0",
        doc={"arr1": [0], "arr2": [DOUBLE_ZERO]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should treat integer zero and double zero as equivalent",
    ),
    ExpressionTestCase(
        "int0_vs_long0",
        doc={"arr1": [0], "arr2": [INT64_ZERO]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should treat integer zero and long zero as equivalent",
    ),
    ExpressionTestCase(
        "int0_vs_decimal0",
        doc={"arr1": [0], "arr2": [DECIMAL128_ZERO]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should treat integer zero and decimal128 zero as equivalent",
    ),
    ExpressionTestCase(
        "double_neg0_vs_0",
        doc={"arr1": [DOUBLE_NEGATIVE_ZERO, 1], "arr2": [DOUBLE_ZERO]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat double negative zero as equivalent to positive zero",
    ),
    ExpressionTestCase(
        "decimal_neg0_vs_0",
        doc={"arr1": [DECIMAL128_NEGATIVE_ZERO, 1], "arr2": [DECIMAL128_ZERO]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat decimal128 negative zero as equivalent to positive zero",
    ),
    ExpressionTestCase(
        "double_neg0_vs_int0",
        doc={"arr1": [DOUBLE_NEGATIVE_ZERO, 1], "arr2": [0]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat double negative zero as equivalent to integer zero",
    ),
    ExpressionTestCase(
        "decimal_neg0_vs_int0",
        doc={"arr1": [DECIMAL128_NEGATIVE_ZERO, 1], "arr2": [0]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should treat decimal128 negative zero as equivalent to integer zero",
    ),
    ExpressionTestCase(
        "long_vs_decimal_pair",
        doc={"arr1": [Int64(1), Int64(2)], "arr2": [Decimal128("1"), Decimal128("2")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when long and decimal128 pairs are equivalent",
    ),
    ExpressionTestCase(
        "all_numeric_types_equiv",
        doc={"arr1": [1, 2, 3], "arr2": [1.0, Int64(2), 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when mixed numeric types are all equivalent",
    ),
]

# Property [Object Comparison]: objects are equal only when keys, values, and key
# order all match.
SETDIFFERENCE_OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "identical_objects",
        doc={"arr1": [{"a": 1, "b": 2}], "arr2": [{"a": 1, "b": 2}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for identical objects with same key order",
    ),
    ExpressionTestCase(
        "same_keys_diff_values",
        doc={"arr1": [{"a": 1}], "arr2": [{"a": 2}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[{"a": 1}],
        msg="Should treat objects with same keys but different values as distinct",
    ),
    ExpressionTestCase(
        "different_keys",
        doc={"arr1": [{"a": 1}], "arr2": [{"b": 1}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[{"a": 1}],
        msg="Should treat objects with different keys as distinct",
    ),
    ExpressionTestCase(
        "nested_objects",
        doc={"arr1": [{"a": {"b": 1}}], "arr2": [{"a": {"b": 1}}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for identical nested objects",
    ),
    ExpressionTestCase(
        "nested_objects_diff",
        doc={"arr1": [{"a": {"b": 1}}], "arr2": [{"a": {"b": 2}}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[{"a": {"b": 1}}],
        msg="Should treat nested objects with different values as distinct",
    ),
    ExpressionTestCase(
        "empty_objects",
        doc={"arr1": [{}], "arr2": [{}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for identical empty objects",
    ),
    ExpressionTestCase(
        "empty_vs_nonempty",
        doc={"arr1": [{}, {"a": 1}], "arr2": [{}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[{"a": 1}],
        msg="Should treat empty and non-empty objects as distinct elements",
    ),
    ExpressionTestCase(
        "object_with_multiple_elements",
        doc={"arr1": [{"a": 1}, {"a": 2}, {"a": 3}], "arr2": [{"a": 1}, {"a": 2}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[{"a": 3}],
        msg="Should handle difference with multiple object elements",
    ),
    ExpressionTestCase(
        "object_key_order",
        doc={"arr1": [{"a": 1, "b": 2}], "arr2": [{"b": 2, "a": 1}]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[{"a": 1, "b": 2}],
        msg="Should treat objects with different key order as distinct",
    ),
]

# Property [BSON Element Types]: dates, ObjectIds, binary, timestamps, and
# min/max keys compare by their own type-specific equality.
SETDIFFERENCE_BSON_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_remove_subset",
        doc={
            "arr1": [1, "a", True, None, datetime(2024, 1, 1, tzinfo=timezone.utc)],
            "arr2": [1, True],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", None, datetime(2024, 1, 1, tzinfo=timezone.utc)],
        msg="Should remove subset of mixed BSON types and preserve the rest",
    ),
    ExpressionTestCase(
        "mixed_remove_all",
        doc={"arr1": [1, "a", True], "arr2": [1, "a", True]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when all mixed BSON type elements are removed",
    ),
    ExpressionTestCase(
        "date_remove",
        doc={
            "arr1": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            ],
            "arr2": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[datetime(2024, 1, 2, tzinfo=timezone.utc)],
        msg="Should handle date element comparison correctly",
    ),
    ExpressionTestCase(
        "objectid_remove",
        doc={
            "arr1": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
            "arr2": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
        msg="Should handle ObjectId element comparison correctly",
    ),
    ExpressionTestCase(
        "objectid_no_match",
        doc={
            "arr1": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")],
            "arr2": [ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")],
        msg="Should preserve ObjectId when it does not match any in second array",
    ),
    ExpressionTestCase(
        "binary_remove",
        doc={
            "arr1": [Binary(b"\x01\x02\x03", 0), Binary(b"\x04\x05\x06", 0)],
            "arr2": [Binary(b"\x01\x02\x03", 0)],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[b"\x04\x05\x06"],
        msg="Should handle binary data element comparison correctly",
    ),
    ExpressionTestCase(
        "timestamp_remove",
        doc={"arr1": [Timestamp(1000, 1), Timestamp(2000, 1)], "arr2": [Timestamp(1000, 1)]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Timestamp(2000, 1)],
        msg="Should handle timestamp element comparison correctly",
    ),
    ExpressionTestCase(
        "timestamp_diff_increment",
        doc={"arr1": [Timestamp(1000, 1)], "arr2": [Timestamp(1000, 2)]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Timestamp(1000, 1)],
        msg="Should treat timestamps with different increments as distinct elements",
    ),
    ExpressionTestCase(
        "minkey_remove",
        doc={"arr1": [MinKey(), 1, "a"], "arr2": [MinKey()]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, "a"],
        msg="Should remove MinKey element when it appears in second array",
    ),
    ExpressionTestCase(
        "maxkey_remove",
        doc={"arr1": [MaxKey(), 1, "a"], "arr2": [MaxKey()]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, "a"],
        msg="Should remove MaxKey element when it appears in second array",
    ),
    ExpressionTestCase(
        "minkey_vs_maxkey",
        doc={"arr1": [MinKey(), MaxKey()], "arr2": [MinKey()]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[MaxKey()],
        msg="Should treat MinKey and MaxKey as distinct elements",
    ),
    ExpressionTestCase(
        "both_minmax",
        doc={"arr1": [MinKey(), MaxKey()], "arr2": [MinKey(), MaxKey()]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when both MinKey and MaxKey are removed",
    ),
    ExpressionTestCase(
        "regex_remove",
        doc={"arr1": [Regex("abc", "i"), Regex("def", "")], "arr2": [Regex("abc", "i")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Regex("def", "")],
        msg="Should handle regex element comparison correctly",
    ),
    ExpressionTestCase(
        "regex_dedup",
        doc={"arr1": [Regex("abc", ""), Regex("abc", "")], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Regex("abc", "")],
        msg="Should deduplicate identical regex elements",
    ),
    ExpressionTestCase(
        "regex_different_flags",
        doc={"arr1": [Regex("abc", "i"), Regex("abc", "")], "arr2": [Regex("abc", "")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Regex("abc", "i")],
        msg="Should treat regex with different flags as distinct elements",
    ),
    ExpressionTestCase(
        "javascript_remove",
        doc={"arr1": [Code("function(){}"), Code("other()")], "arr2": [Code("function(){}")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Code("other()")],
        msg="Should handle javascript code element comparison correctly",
    ),
    ExpressionTestCase(
        "javascript_dedup",
        doc={"arr1": [Code("function(){}"), Code("function(){}")], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Code("function(){}")],
        msg="Should deduplicate identical javascript code elements",
    ),
    ExpressionTestCase(
        "special_values_remove_null_nan",
        doc={
            "arr1": [None, FLOAT_NAN, MinKey(), FLOAT_INFINITY, MaxKey()],
            "arr2": [None, DECIMAL128_NAN],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[MinKey(), FLOAT_INFINITY, MaxKey()],
        msg="Should remove null and NaN while preserving other special values",
    ),
    ExpressionTestCase(
        "mixed_null_timestamp",
        doc={"arr1": [None, False, True, Timestamp(1, 1)], "arr2": [True, False, None]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Timestamp(1, 1)],
        msg="Should preserve timestamp when null and boolean elements are removed",
    ),
]

# Property [Decimal128 Equivalence]: decimal128 values compare by numeric value,
# so representation differences do not matter.
SETDIFFERENCE_DECIMAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "trailing_zeros",
        doc={"arr1": [DECIMAL128_TRAILING_ZERO], "arr2": [Decimal128("1.00")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should treat decimal128 values with trailing zeros as equivalent",
    ),
    ExpressionTestCase(
        "exponent_notation",
        doc={"arr1": [Decimal128("1E+2")], "arr2": [Decimal128("100")]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should treat decimal128 exponent notation as equivalent to expanded form",
    ),
    ExpressionTestCase(
        "high_precision_match",
        doc={
            "arr1": [Decimal128("1.000000000000000000000000000000001")],
            "arr2": [Decimal128("1.000000000000000000000000000000001")],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for identical high-precision decimal128 values",
    ),
    ExpressionTestCase(
        "high_precision_mismatch",
        doc={
            "arr1": [Decimal128("1.000000000000000000000000000000001")],
            "arr2": [Decimal128("1.000000000000000000000000000000002")],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Decimal128("1.000000000000000000000000000000001")],
        msg="Should treat high-precision decimal128 values differing in last digit as distinct",
    ),
]

# Property [String Comparison]: strings compare by exact code points, including
# unicode and emoji.
SETDIFFERENCE_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unicode",
        doc={"arr1": ["café", "naïve"], "arr2": ["café", "résumé"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["naïve"],
        msg="Should handle unicode string comparison correctly",
    ),
    ExpressionTestCase(
        "emoji",
        doc={"arr1": ["🎉", "🎊"], "arr2": ["🎉", "🎈"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["🎊"],
        msg="Should handle emoji string comparison correctly",
    ),
]

SETDIFFERENCE_TYPE_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_BSON_DISTINCTION_TESTS
    + SETDIFFERENCE_NAN_TESTS
    + SETDIFFERENCE_INFINITY_TESTS
    + SETDIFFERENCE_NUMERIC_EQUIV_TESTS
    + SETDIFFERENCE_OBJECT_TESTS
    + SETDIFFERENCE_BSON_ELEMENT_TESTS
    + SETDIFFERENCE_DECIMAL_TESTS
    + SETDIFFERENCE_STRING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETDIFFERENCE_TYPE_TESTS))
def test_setDifference_types(collection, test):
    """Test $setDifference type handling with field-reference array operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
