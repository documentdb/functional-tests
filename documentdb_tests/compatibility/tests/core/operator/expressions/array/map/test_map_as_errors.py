"""
Error tests for $map 'as' parameter.

Tests that $map rejects non-string 'as' values (including empty string).
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
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, FLOAT_NAN

# Property [Invalid As Type]: $map rejects non-string types for the as parameter.
INVALID_AS_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "type_int",
        expression={"$map": {"input": [1, 2, 3], "as": 1, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject int as variable name",
    ),
    ExpressionTestCase(
        "type_long",
        expression={"$map": {"input": [1, 2, 3], "as": Int64(1), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject Int64 as variable name",
    ),
    ExpressionTestCase(
        "type_object",
        expression={"$map": {"input": [1, 2, 3], "as": {"a": 1}, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject object as variable name",
    ),
    ExpressionTestCase(
        "type_array",
        expression={"$map": {"input": [1, 2, 3], "as": [1], "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject array as variable name",
    ),
    ExpressionTestCase(
        "type_minkey",
        expression={"$map": {"input": [1, 2, 3], "as": MinKey(), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject MinKey as variable name",
    ),
    ExpressionTestCase(
        "type_maxkey",
        expression={"$map": {"input": [1, 2, 3], "as": MaxKey(), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject MaxKey as variable name",
    ),
    ExpressionTestCase(
        "type_bindata",
        expression={"$map": {"input": [1, 2, 3], "as": Binary(b"\x00", 0), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject Binary as variable name",
    ),
    ExpressionTestCase(
        "type_objectid",
        expression={"$map": {"input": [1, 2, 3], "as": ObjectId(), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject ObjectId as variable name",
    ),
    ExpressionTestCase(
        "type_date",
        expression={"$map": {"input": [1, 2, 3], "as": datetime(2026, 1, 1), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject datetime as variable name",
    ),
    ExpressionTestCase(
        "type_timestamp",
        expression={"$map": {"input": [1, 2, 3], "as": Timestamp(0, 0), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject Timestamp as variable name",
    ),
    ExpressionTestCase(
        "type_regex",
        expression={"$map": {"input": [1, 2, 3], "as": Regex("pattern"), "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject Regex as variable name",
    ),
    ExpressionTestCase(
        "type_bool_true",
        expression={"$map": {"input": [1, 2, 3], "as": True, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject boolean as variable name",
    ),
    ExpressionTestCase(
        "type_null",
        expression={"$map": {"input": [1, 2, 3], "as": None, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject null as variable name",
    ),
    ExpressionTestCase(
        "type_empty_string",
        expression={"$map": {"input": [1, 2, 3], "as": "", "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject empty string as variable name",
    ),
    ExpressionTestCase(
        "type_nan",
        expression={"$map": {"input": [1, 2, 3], "as": FLOAT_NAN, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject NaN as variable name",
    ),
    ExpressionTestCase(
        "type_infinity",
        expression={"$map": {"input": [1, 2, 3], "as": FLOAT_INFINITY, "in": "$$this"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$map should reject Infinity as variable name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_AS_TYPE_TESTS))
def test_map_invalid_as(collection, test):
    """Test $map with invalid 'as' parameter values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
