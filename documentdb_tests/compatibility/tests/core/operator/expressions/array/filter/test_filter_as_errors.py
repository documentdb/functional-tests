"""
Error tests for $filter 'as' parameter.

Tests invalid 'as' types.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

INVALID_AS_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="type_int",
        expression={"$filter": {"input": [1, 2, 3], "as": 1, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=int should error",
    ),
    ExpressionTestCase(
        id="type_long",
        expression={"$filter": {"input": [1, 2, 3], "as": Int64(1), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Int64 should error",
    ),
    ExpressionTestCase(
        id="type_object",
        expression={"$filter": {"input": [1, 2, 3], "as": {"a": 1}, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=object should error",
    ),
    ExpressionTestCase(
        id="type_array",
        expression={"$filter": {"input": [1, 2, 3], "as": [1], "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=array should error",
    ),
    ExpressionTestCase(
        id="type_minkey",
        expression={"$filter": {"input": [1, 2, 3], "as": MinKey(), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=MinKey should error",
    ),
    ExpressionTestCase(
        id="type_maxkey",
        expression={"$filter": {"input": [1, 2, 3], "as": MaxKey(), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=MaxKey should error",
    ),
    ExpressionTestCase(
        id="type_bindata",
        expression={"$filter": {"input": [1, 2, 3], "as": Binary(b"\x00", 0), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Binary should error",
    ),
    ExpressionTestCase(
        id="type_objectid",
        expression={"$filter": {"input": [1, 2, 3], "as": ObjectId(), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=ObjectId should error",
    ),
    ExpressionTestCase(
        id="type_date",
        expression={
            "$filter": {
                "input": [1, 2, 3],
                "as": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "cond": True,
            }
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=datetime should error",
    ),
    ExpressionTestCase(
        id="type_timestamp",
        expression={"$filter": {"input": [1, 2, 3], "as": Timestamp(0, 0), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Timestamp should error",
    ),
    ExpressionTestCase(
        id="type_regex",
        expression={"$filter": {"input": [1, 2, 3], "as": Regex("pattern"), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=Regex should error",
    ),
    ExpressionTestCase(
        id="type_bool_true",
        expression={"$filter": {"input": [1, 2, 3], "as": True, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=True should error",
    ),
    ExpressionTestCase(
        id="type_null",
        expression={"$filter": {"input": [1, 2, 3], "as": None, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=None should error",
    ),
    ExpressionTestCase(
        id="type_empty_string",
        expression={"$filter": {"input": [1, 2, 3], "as": "", "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as='' should error",
    ),
    ExpressionTestCase(
        id="type_nan",
        expression={"$filter": {"input": [1, 2, 3], "as": float("nan"), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=NaN should error",
    ),
    ExpressionTestCase(
        id="type_infinity",
        expression={"$filter": {"input": [1, 2, 3], "as": float("inf"), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="as=inf should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_AS_TYPE_TESTS))
def test_filter_invalid_as(collection, test):
    """Test $filter with invalid 'as' parameter values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
