"""Tests for $and argument handling — count variations, formats, scalar/array input."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS = [
    ExpressionTestCase(
        "empty_array",
        expression={"$and": []},
        expected=True,
        msg="Should return true for empty array",
    ),
    ExpressionTestCase(
        "two_args_true_false",
        expression={"$and": [True, False]},
        expected=False,
        msg="Should return false when any is false",
    ),
    ExpressionTestCase(
        "two_args_all_true",
        expression={"$and": [True, 1]},
        expected=True,
        msg="Should return true when all true",
    ),
    ExpressionTestCase(
        "large_all_true",
        expression={"$and": [True] * 100},
        expected=True,
        msg="Should return true for 100 true values",
    ),
    ExpressionTestCase(
        "large_last_false",
        expression={"$and": [True] * 99 + [False]},
        expected=False,
        msg="Should return false with last false in 100",
    ),
    ExpressionTestCase(
        "array_element_truthy",
        expression={"$and": [[]]},
        expected=True,
        msg="Should return true for array element (truthy)",
    ),
    ExpressionTestCase(
        "non_array_true",
        expression={"$and": True},
        expected=True,
        msg="Should return true for non-array true",
    ),
    ExpressionTestCase(
        "non_array_null",
        expression={"$and": None},
        expected=False,
        msg="Should return false for non-array null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_argument_handling(collection, test):
    """Test $and argument handling."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
