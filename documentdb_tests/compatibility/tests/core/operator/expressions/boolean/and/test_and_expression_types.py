"""Tests for $and with nested $and expressions."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

NESTED_AND_TESTS = [
    ExpressionTestCase(
        "nested_and_mixed",
        expression={"$and": [{"$and": [True]}, {"$and": [False]}]},
        expected=False,
        msg="Nested $and with mixed returns false",
    ),
    ExpressionTestCase(
        "nested_and_inner_true",
        expression={"$and": [{"$and": [True, True]}, True]},
        expected=True,
        msg="Nested $and with inner true should return true",
    ),
    ExpressionTestCase(
        "nested_and_all_true",
        expression={"$and": [{"$and": [True, True]}, {"$and": [True, True]}]},
        expected=True,
        msg="Nested $and with all true should return true",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_AND_TESTS))
def test_and_nested_self(collection, test):
    """Test $and nested inside $and."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
