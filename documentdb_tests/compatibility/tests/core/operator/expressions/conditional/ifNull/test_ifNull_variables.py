"""
Tests for $ifNull with system and user-defined variables.

Covers $$CURRENT and $let variable resolution.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

SYSTEM_VARIABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "current_variable",
        doc={"a": 1},
        expression={"$ifNull": ["$$CURRENT.a", "default"]},
        expected=1,
        msg="$$CURRENT.a should resolve to field value",
    ),
    ExpressionTestCase(
        "let_variable_non_null",
        doc={"a": None},
        expression={"$let": {"vars": {"x": 10}, "in": {"$ifNull": ["$a", "$$x"]}}},
        expected=10,
        msg="Should return $let variable value when input is null",
    ),
    ExpressionTestCase(
        "let_variable_null",
        doc={"a": None},
        expression={"$let": {"vars": {"x": None}, "in": {"$ifNull": ["$$x", "default"]}}},
        expected="default",
        msg="Should return default when $let variable is null",
    ),
]

ALL_TESTS = SYSTEM_VARIABLE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ifNull_system_variables(collection, test):
    """Test $ifNull with system variables."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
