"""Tests for $or argument handling — count variations, formats, scalar/array input."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)

ALL_TESTS = [
    ExpressionTestCase(
        "empty_array",
        expression={"$or": []},
        expected=False,
        msg="Should return false for empty array",
    ),
    ExpressionTestCase(
        "two_args_true_false",
        expression={"$or": [True, False]},
        expected=True,
        msg="Should return true when any is true",
    ),
    ExpressionTestCase(
        "two_args_all_false",
        expression={"$or": [0, False]},
        expected=False,
        msg="Should return false when all false",
    ),
    ExpressionTestCase(
        "large_all_false",
        expression={"$or": [False] * 100},
        expected=False,
        msg="Should return false for 100 false values",
    ),
    ExpressionTestCase(
        "large_last_true",
        expression={"$or": [False] * 99 + [True]},
        expected=True,
        msg="Should return true with last true in 100",
    ),
    ExpressionTestCase(
        "array_element_truthy",
        expression={"$or": [[]]},
        expected=True,
        msg="Should return true for array element (truthy)",
    ),
    ExpressionTestCase(
        "non_array_true",
        expression={"$or": True},
        expected=True,
        msg="Should return true for non-array true",
    ),
    ExpressionTestCase(
        "non_array_null",
        expression={"$or": None},
        expected=False,
        msg="Should return false for non-array null",
    ),
]


@pytest.mark.parametrize("test", ALL_TESTS, ids=lambda t: t.id)
def test_or_argument_handling(collection, test):
    """Test $or argument handling."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
