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
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
)

INVALID_AS_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "type_int",
        expression={"$filter": {"input": [1, 2, 3], "as": 1, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject int as variable name",
    ),
    ExpressionTestCase(
        "type_long",
        expression={"$filter": {"input": [1, 2, 3], "as": Int64(1), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject Int64 as variable name",
    ),
    ExpressionTestCase(
        "type_object",
        expression={"$filter": {"input": [1, 2, 3], "as": {"a": 1}, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject object as variable name",
    ),
    ExpressionTestCase(
        "type_array",
        expression={"$filter": {"input": [1, 2, 3], "as": [1], "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject array as variable name",
    ),
    ExpressionTestCase(
        "type_minkey",
        expression={"$filter": {"input": [1, 2, 3], "as": MinKey(), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject MinKey as variable name",
    ),
    ExpressionTestCase(
        "type_maxkey",
        expression={"$filter": {"input": [1, 2, 3], "as": MaxKey(), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject MaxKey as variable name",
    ),
    ExpressionTestCase(
        "type_bindata",
        expression={"$filter": {"input": [1, 2, 3], "as": Binary(b"\x00", 0), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject Binary as variable name",
    ),
    ExpressionTestCase(
        "type_objectid",
        expression={"$filter": {"input": [1, 2, 3], "as": ObjectId(), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject ObjectId as variable name",
    ),
    ExpressionTestCase(
        "type_date",
        expression={
            "$filter": {
                "input": [1, 2, 3],
                "as": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "cond": True,
            }
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject datetime as variable name",
    ),
    ExpressionTestCase(
        "type_timestamp",
        expression={"$filter": {"input": [1, 2, 3], "as": Timestamp(0, 0), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject Timestamp as variable name",
    ),
    ExpressionTestCase(
        "type_regex",
        expression={"$filter": {"input": [1, 2, 3], "as": Regex("pattern"), "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject Regex as variable name",
    ),
    ExpressionTestCase(
        "type_bool_true",
        expression={"$filter": {"input": [1, 2, 3], "as": True, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject True as variable name",
    ),
    ExpressionTestCase(
        "type_null",
        expression={"$filter": {"input": [1, 2, 3], "as": None, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject None as variable name",
    ),
    ExpressionTestCase(
        "type_empty_string",
        expression={"$filter": {"input": [1, 2, 3], "as": "", "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject '' as variable name",
    ),
    ExpressionTestCase(
        "type_nan",
        expression={"$filter": {"input": [1, 2, 3], "as": FLOAT_NAN, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject NaN as variable name",
    ),
    ExpressionTestCase(
        "type_infinity",
        expression={"$filter": {"input": [1, 2, 3], "as": FLOAT_INFINITY, "cond": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$filter should reject inf as variable name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_AS_TYPE_TESTS))
def test_filter_invalid_as(collection, test):
    """Test $filter with invalid 'as' parameter values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
