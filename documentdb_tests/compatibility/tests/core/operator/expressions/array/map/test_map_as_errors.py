"""
Error tests for $map 'as' parameter.

Tests invalid 'as' types, invalid variable names, and reserved variable names.
"""

from datetime import datetime

import pytest
from bson import Binary, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

INVALID_AS_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="type_int",
        expression={"$map": {"input": [1, 2, 3], "as": 1, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=int should error",
    ),
    ExpressionTestCase(
        id="type_long",
        expression={"$map": {"input": [1, 2, 3], "as": Int64(1), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Int64 should error",
    ),
    ExpressionTestCase(
        id="type_object",
        expression={"$map": {"input": [1, 2, 3], "as": {"a": 1}, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=object should error",
    ),
    ExpressionTestCase(
        id="type_array",
        expression={"$map": {"input": [1, 2, 3], "as": [1], "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=array should error",
    ),
    ExpressionTestCase(
        id="type_minkey",
        expression={"$map": {"input": [1, 2, 3], "as": MinKey(), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=MinKey should error",
    ),
    ExpressionTestCase(
        id="type_maxkey",
        expression={"$map": {"input": [1, 2, 3], "as": MaxKey(), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=MaxKey should error",
    ),
    ExpressionTestCase(
        id="type_bindata",
        expression={"$map": {"input": [1, 2, 3], "as": Binary(b"\x00", 0), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Binary should error",
    ),
    ExpressionTestCase(
        id="type_objectid",
        expression={"$map": {"input": [1, 2, 3], "as": ObjectId(), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=ObjectId should error",
    ),
    ExpressionTestCase(
        id="type_date",
        expression={"$map": {"input": [1, 2, 3], "as": datetime(2026, 1, 1), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=datetime should error",
    ),
    ExpressionTestCase(
        id="type_timestamp",
        expression={"$map": {"input": [1, 2, 3], "as": Timestamp(0, 0), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Timestamp should error",
    ),
    ExpressionTestCase(
        id="type_regex",
        expression={"$map": {"input": [1, 2, 3], "as": Regex("pattern"), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Regex should error",
    ),
    ExpressionTestCase(
        id="type_bool_true",
        expression={"$map": {"input": [1, 2, 3], "as": True, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=True should error",
    ),
    ExpressionTestCase(
        id="type_null",
        expression={"$map": {"input": [1, 2, 3], "as": None, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=None should error",
    ),
    ExpressionTestCase(
        id="type_empty_string",
        expression={"$map": {"input": [1, 2, 3], "as": "", "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as='' should error",
    ),
    ExpressionTestCase(
        id="type_nan",
        expression={"$map": {"input": [1, 2, 3], "as": float("nan"), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=NaN should error",
    ),
    ExpressionTestCase(
        id="type_infinity",
        expression={"$map": {"input": [1, 2, 3], "as": float("inf"), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=inf should error",
    ),
]

ALL_AS_TESTS = INVALID_AS_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_AS_TESTS))
def test_map_invalid_as(collection, test):
    """Test $map with invalid 'as' parameter values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
