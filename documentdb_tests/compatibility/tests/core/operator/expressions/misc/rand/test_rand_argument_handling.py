"""
Tests for $rand argument handling and error cases.
"""

from datetime import datetime

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
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_NOT_OBJECT_ERROR,
    RAND_UNEXPECTED_ARG_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING


def test_rand_empty_array_type(collection):
    """Test rand with empty array argument returns double type."""
    result = execute_expression(collection, {"$type": {"$rand": []}})
    assert_expression_result(result, expected="double")


def test_rand_empty_array_range(collection):
    """Test rand with empty array argument returns value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$rand": []}},
                "in": {"$and": [{"$gte": ["$$r", 0.0]}, {"$lt": ["$$r", 1.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True)


INVALID_INPUTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_1",
        expression={"$rand": 1},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for integer argument",
    ),
    ExpressionTestCase(
        "int_0",
        expression={"$rand": 0},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for zero argument",
    ),
    ExpressionTestCase(
        "int_neg1",
        expression={"$rand": -1},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for negative integer argument",
    ),
    ExpressionTestCase(
        "int_2",
        expression={"$rand": 2},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for integer 2 argument",
    ),
    ExpressionTestCase(
        "string",
        expression={"$rand": "string"},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for string argument",
    ),
    ExpressionTestCase(
        "null",
        expression={"$rand": None},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for null argument",
    ),
    ExpressionTestCase(
        "bool_true",
        expression={"$rand": True},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for boolean true argument",
    ),
    ExpressionTestCase(
        "bool_false",
        expression={"$rand": False},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for boolean false argument",
    ),
    ExpressionTestCase(
        "double",
        expression={"$rand": 1.5},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for double argument",
    ),
    ExpressionTestCase(
        "decimal128",
        expression={"$rand": Decimal128("1")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for Decimal128 argument",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$rand": Decimal128("NaN")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for Decimal128 NaN argument",
    ),
    ExpressionTestCase(
        "decimal128_inf",
        expression={"$rand": Decimal128("Infinity")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for Decimal128 Infinity argument",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf",
        expression={"$rand": Decimal128("-Infinity")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for Decimal128 negative Infinity argument",
    ),
    ExpressionTestCase(
        "long",
        expression={"$rand": Int64(1)},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for long argument",
    ),
    ExpressionTestCase(
        "date",
        expression={"$rand": datetime(2024, 1, 1)},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for date argument",
    ),
    ExpressionTestCase(
        "objectid",
        expression={"$rand": ObjectId("000000000000000000000000")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for ObjectId argument",
    ),
    ExpressionTestCase(
        "regex",
        expression={"$rand": Regex(".*")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for regex argument",
    ),
    ExpressionTestCase(
        "javascript",
        expression={"$rand": Code("function(){}")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for JavaScript argument",
    ),
    ExpressionTestCase(
        "timestamp",
        expression={"$rand": Timestamp(0, 1)},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for Timestamp argument",
    ),
    ExpressionTestCase(
        "minkey",
        expression={"$rand": MinKey()},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for MinKey argument",
    ),
    ExpressionTestCase(
        "maxkey",
        expression={"$rand": MaxKey()},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for MaxKey argument",
    ),
    ExpressionTestCase(
        "binary",
        expression={"$rand": Binary(b"")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for binary argument",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$rand": float("nan")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for float NaN argument",
    ),
    ExpressionTestCase(
        "float_inf",
        expression={"$rand": float("inf")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for float Infinity argument",
    ),
    ExpressionTestCase(
        "float_neg_inf",
        expression={"$rand": float("-inf")},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for float negative Infinity argument",
    ),
    ExpressionTestCase(
        "array_with_int",
        expression={"$rand": [1]},
        error_code=RAND_UNEXPECTED_ARG_ERROR,
        msg="Should error for non-empty array with integer",
    ),
    ExpressionTestCase(
        "array_with_object",
        expression={"$rand": [{}]},
        error_code=RAND_UNEXPECTED_ARG_ERROR,
        msg="Should error for non-empty array with object",
    ),
    ExpressionTestCase(
        "array_with_array",
        expression={"$rand": [[]]},
        error_code=RAND_UNEXPECTED_ARG_ERROR,
        msg="Should error for non-empty array with nested array",
    ),
    ExpressionTestCase(
        "array_with_two_objects",
        expression={"$rand": [{}, {}]},
        error_code=RAND_UNEXPECTED_ARG_ERROR,
        msg="Should error for array with two objects",
    ),
    ExpressionTestCase(
        "object_with_field",
        expression={"$rand": {"a": 1}},
        error_code=RAND_UNEXPECTED_ARG_ERROR,
        msg="Should error for non-empty object with field",
    ),
    ExpressionTestCase(
        "object_with_null",
        expression={"$rand": {"a": None}},
        error_code=RAND_UNEXPECTED_ARG_ERROR,
        msg="Should error for non-empty object with null field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_INPUTS))
def test_rand_invalid_inputs(collection, test):
    """Test rand rejects non-empty array and object arguments."""
    result = execute_expression(collection, test.expression)
    assertResult(result, error_code=test.error_code, msg=test.msg)


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_scalar",
        expression={"$rand": "$a"},
        doc={"a": 1},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for field reference to scalar",
    ),
    ExpressionTestCase(
        "missing_field_ref",
        expression={"$rand": "$not_exist"},
        doc={},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for missing field reference",
    ),
    ExpressionTestCase(
        "missing_constant",
        expression={"$rand": MISSING},
        doc={},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for missing constant field reference",
    ),
    ExpressionTestCase(
        "field_ref_object",
        expression={"$rand": "$a"},
        doc={"a": {}},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for field reference resolving to object",
    ),
    ExpressionTestCase(
        "field_ref_array",
        expression={"$rand": "$a"},
        doc={"a": []},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Should error for field reference resolving to array",
    ),
    ExpressionTestCase(
        "array_missing_ref",
        expression={"$rand": ["$not_exist"]},
        doc={},
        error_code=RAND_UNEXPECTED_ARG_ERROR,
        msg="Should error for array with missing field reference",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_TESTS))
def test_rand_field_ref_errors(collection, test):
    """Test rand rejects field reference arguments."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertResult(result, error_code=test.error_code, msg=test.msg)
