"""Tests for $not expression argument handling and error cases."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

WRONG_ARG_COUNT_TESTS = [
    ExpressionTestCase(
        "not_arg_empty_array",
        expression={"$not": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="empty array should error",
    ),
    ExpressionTestCase(
        "not_arg_two_args",
        expression={"$not": [True, False]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="two args should error",
    ),
    ExpressionTestCase(
        "not_arg_three_args",
        expression={"$not": [True, False, True]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="three args should error",
    ),
]

NON_ARRAY_FORMAT_TESTS = [
    ExpressionTestCase(
        "not_arg_non_array_true",
        expression={"$not": True},
        expected=False,
        msg="scalar true evaluates as truthy",
    ),
    ExpressionTestCase(
        "not_arg_non_array_null",
        expression={"$not": None},
        expected=True,
        msg="scalar null evaluates as falsy",
    ),
    ExpressionTestCase(
        "not_arg_non_array_zero",
        expression={"$not": 0},
        expected=True,
        msg="scalar 0 evaluates as falsy",
    ),
]

ALL_TESTS = WRONG_ARG_COUNT_TESTS + NON_ARRAY_FORMAT_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_argument_handling(collection, test):
    """Test $not argument count variations and error cases."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


ERROR_PROPAGATION_TESTS = [
    ExpressionTestCase(
        "not_arg_error_divide_by_zero",
        expression={"$not": [{"$divide": [1, "$x"]}]},
        doc={"x": 0},
        error_code=BAD_VALUE_ERROR,
        msg="$not wrapping divide-by-zero should propagate error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_PROPAGATION_TESTS))
def test_not_error_propagation(collection, test):
    """Test $not propagates errors from inner expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
