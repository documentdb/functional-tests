"""Tests for $not with nested $not expressions."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

NESTED_NOT_TESTS = [
    ExpressionTestCase(
        "not_nested_double_negation_true",
        expression={"$not": [{"$not": [True]}]},
        expected=True,
        msg="$not($not(true)) should return true",
    ),
    ExpressionTestCase(
        "not_nested_double_negation_false",
        expression={"$not": [{"$not": [False]}]},
        expected=False,
        msg="$not($not(false)) should return false",
    ),
    ExpressionTestCase(
        "not_nested_triple_negation",
        expression={"$not": [{"$not": [{"$not": [True]}]}]},
        expected=False,
        msg="$not($not($not(true))) should return false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_NOT_TESTS))
def test_not_nested_self(collection, test):
    """Test $not nested inside $not."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
