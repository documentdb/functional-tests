"""Tests for $or with nested $or expressions."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

NESTED_OR_TESTS = [
    ExpressionTestCase(
        "nested_or_mixed",
        expression={"$or": [{"$or": [False]}, {"$or": [True]}]},
        expected=True,
        msg="Nested $or with mixed returns true",
    ),
    ExpressionTestCase(
        "nested_or_inner_true",
        expression={"$or": [{"$or": [False, True]}, False]},
        expected=True,
        msg="Nested $or with inner true should return true",
    ),
    ExpressionTestCase(
        "nested_or_all_false",
        expression={"$or": [{"$or": [False, False]}, False]},
        expected=False,
        msg="Nested $or with all false should return false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_OR_TESTS))
def test_or_nested_self(collection, test):
    """Test $or nested inside $or."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
