"""
Tests for $ifNull argument handling and error code validation.

Covers invalid argument formats (empty array, single element, non-array types)
and minimum valid argument count.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import IFNULL_INVALID_ARGS_ERROR
from documentdb_tests.framework.parametrize import pytest_params

INVALID_ARG_FORMAT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array",
        expression={"$ifNull": []},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with empty array",
    ),
    ExpressionTestCase(
        "single_element",
        expression={"$ifNull": [1]},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with single element array",
    ),
    ExpressionTestCase(
        "single_null",
        expression={"$ifNull": [None]},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with single null element",
    ),
    ExpressionTestCase(
        "single_field_ref",
        expression={"$ifNull": ["$a"]},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with single field reference",
    ),
    ExpressionTestCase(
        "non_array_string",
        expression={"$ifNull": "$field"},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with non-array string argument",
    ),
    ExpressionTestCase(
        "non_array_int",
        expression={"$ifNull": 123},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with non-array integer argument",
    ),
    ExpressionTestCase(
        "non_array_null",
        expression={"$ifNull": None},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with null argument",
    ),
    ExpressionTestCase(
        "non_array_bool",
        expression={"$ifNull": True},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with boolean argument",
    ),
    ExpressionTestCase(
        "non_array_object",
        expression={"$ifNull": {"a": 1}},
        error_code=IFNULL_INVALID_ARGS_ERROR,
        msg="Should error with object argument",
    ),
]

VALID_ARG_COUNT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "two_args_minimum",
        expression={"$ifNull": [1, "default"]},
        expected=1,
        msg="Should accept two arguments (minimum valid)",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$ifNull": [None, None, "default"]},
        expected="default",
        msg="Should accept three arguments",
    ),
]

ALL_TESTS = INVALID_ARG_FORMAT_TESTS + VALID_ARG_COUNT_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ifNull_argument_handling(collection, test):
    """Test $ifNull argument handling and error cases."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
