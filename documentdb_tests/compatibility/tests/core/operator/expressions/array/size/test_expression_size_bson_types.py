"""
BSON type tests for $size expression.

Tests $size correctly counts array elements containing specific BSON types,
special numeric values, Decimal128 special values, and null byte strings.
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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [BSON Element Counting]: $size counts each array element regardless of its BSON type.
BSON_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bson_types_mixed",
        expression={"$size": "$arr"},
        doc={
            "arr": [
                Int64(1),
                Decimal128("2"),
                ObjectId("000000000000000000000001"),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=4,
        msg="$size should count mixed BSON-typed elements",
    ),
    ExpressionTestCase(
        "minkey_maxkey",
        expression={"$size": "$arr"},
        doc={"arr": [MinKey(), MaxKey()]},
        expected=2,
        msg="$size should count MinKey and MaxKey elements",
    ),
    ExpressionTestCase(
        "timestamp_element",
        expression={"$size": "$arr"},
        doc={"arr": [Timestamp(0, 0)]},
        expected=1,
        msg="$size should count a Timestamp element",
    ),
    ExpressionTestCase(
        "binary_element",
        expression={"$size": "$arr"},
        doc={"arr": [Binary(b"\x00", 0)]},
        expected=1,
        msg="$size should count a Binary element",
    ),
    ExpressionTestCase(
        "regex_element",
        expression={"$size": "$arr"},
        doc={"arr": [Regex(".*")]},
        expected=1,
        msg="$size should count a Regex element",
    ),
    ExpressionTestCase(
        "int64_element",
        expression={"$size": "$arr"},
        doc={"arr": [Int64(1)]},
        expected=1,
        msg="$size should count an Int64 element",
    ),
    ExpressionTestCase(
        "decimal128_element",
        expression={"$size": "$arr"},
        doc={"arr": [Decimal128("1")]},
        expected=1,
        msg="$size should count a Decimal128 element",
    ),
    ExpressionTestCase(
        "objectid_element",
        expression={"$size": "$arr"},
        doc={"arr": [ObjectId()]},
        expected=1,
        msg="$size should count an ObjectId element",
    ),
    ExpressionTestCase(
        "datetime_element",
        expression={"$size": "$arr"},
        doc={"arr": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        expected=1,
        msg="$size should count a datetime element",
    ),
]

# Property [Special Numeric Elements]: $size counts NaN, Infinity, and negative-zero elements.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "special_numerics_mixed",
        expression={"$size": "$arr"},
        doc={"arr": [DECIMAL128_NAN, FLOAT_NAN, FLOAT_INFINITY]},
        expected=3,
        msg="$size should count special numeric elements",
    ),
    ExpressionTestCase(
        "nan_element",
        expression={"$size": "$arr"},
        doc={"arr": [FLOAT_NAN]},
        expected=1,
        msg="$size should count a NaN element",
    ),
    ExpressionTestCase(
        "inf_element",
        expression={"$size": "$arr"},
        doc={"arr": [FLOAT_INFINITY]},
        expected=1,
        msg="$size should count an Infinity element",
    ),
    ExpressionTestCase(
        "neg_inf_element",
        expression={"$size": "$arr"},
        doc={"arr": [FLOAT_NEGATIVE_INFINITY]},
        expected=1,
        msg="$size should count a -Infinity element",
    ),
    ExpressionTestCase(
        "neg_zero_element",
        expression={"$size": "$arr"},
        doc={"arr": [DOUBLE_NEGATIVE_ZERO]},
        expected=1,
        msg="$size should count a negative zero element",
    ),
]

# Property [Decimal128 Special Elements]: $size counts Decimal128 NaN and Infinity elements.
DECIMAL128_SPECIAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$size": "$arr"},
        doc={"arr": [DECIMAL128_NAN]},
        expected=1,
        msg="$size should count a Decimal128 NaN element",
    ),
    ExpressionTestCase(
        "decimal128_neg_nan",
        expression={"$size": "$arr"},
        doc={"arr": [DECIMAL128_NEGATIVE_NAN]},
        expected=1,
        msg="$size should count a Decimal128 -NaN element",
    ),
    ExpressionTestCase(
        "decimal128_inf",
        expression={"$size": "$arr"},
        doc={"arr": [DECIMAL128_INFINITY]},
        expected=1,
        msg="$size should count a Decimal128 Infinity element",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf",
        expression={"$size": "$arr"},
        doc={"arr": [DECIMAL128_NEGATIVE_INFINITY]},
        expected=1,
        msg="$size should count a Decimal128 -Infinity element",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero",
        expression={"$size": "$arr"},
        doc={"arr": [DECIMAL128_NEGATIVE_ZERO]},
        expected=1,
        msg="$size should count a Decimal128 -0 element",
    ),
]

# Property [Top-Level Counting]: $size counts only top-level elements, not nested values.
NESTED_MIXED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_mixed_bson",
        expression={"$size": "$arr"},
        doc={
            "arr": [
                MinKey(),
                {"a": [DECIMAL128_ONE_AND_HALF]},
                Int64(1),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                Binary(b"\x01", 0),
            ]
        },
        expected=5,
        msg="$size should count nested mixed BSON elements at the top level",
    ),
]

# Property [Null Byte Strings]: $size counts elements whose string content contains null bytes.
NULL_BYTE_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_byte_strings",
        expression={"$size": "$arr"},
        doc={
            "arr": [
                "\u0000",
                "\u0000abcd",
                "abcd\u0000",
                "1\u00002\u00003\u00004",
                ["\u0000", "\u0000abc", "abc\u0000", "1\u00002\u00003\u0000"],
                {"test_doc": "1\u00002\u00003\u0000"},
                {"test_doc": ["\u0000"]},
            ]
        },
        expected=7,
        msg="$size should count elements whose strings contain null bytes",
    ),
]

ALL_BSON_TESTS = (
    BSON_ELEMENT_TESTS
    + SPECIAL_NUMERIC_TESTS
    + DECIMAL128_SPECIAL_TESTS
    + NESTED_MIXED_BSON_TESTS
    + NULL_BYTE_STRING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_size_bson_insert(collection, test):
    """Test $size BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Literal BSON Input]: $size counts a literal array of BSON-typed elements.
BSON_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_bson_mixed",
        expression={
            "$size": {
                "$literal": [
                    Int64(1),
                    Decimal128("2"),
                    ObjectId("000000000000000000000001"),
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                ]
            }
        },
        expected=4,
        msg="$size should count a literal array of BSON-typed elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSON_LITERAL_TESTS))
def test_size_bson_literal(collection, test):
    """Test $size BSON types with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
