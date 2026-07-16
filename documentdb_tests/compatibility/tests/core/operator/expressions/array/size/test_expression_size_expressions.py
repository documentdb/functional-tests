"""
Expression and field path tests for $size expression.

Tests nested expressions, field path lookups, and composite paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Variable Input]: $size counts an array bound to a $let variable.
LET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_let_variable",
        expression={"$let": {"vars": {"arr": "$arr"}, "in": {"$size": "$$arr"}}},
        doc={"arr": [1, 2, 3]},
        expected=3,
        msg="$size should count an array bound to a $let variable",
    ),
]

# Property [Field Path Input]: $size resolves a field path to an array before counting.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        expression={"$size": "$a.b"},
        doc={"a": {"b": [10, 20, 30]}},
        expected=3,
        msg="$size should count an array at a nested field path",
    ),
    ExpressionTestCase(
        "composite_array_path",
        expression={"$size": "$a.b"},
        doc={"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        expected=3,
        msg="$size should count an array resolved from a composite path",
    ),
]

# Property [Nested Operator Input]: $size counts an array produced by a nested expression.
NESTED_OPERATOR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_operator",
        expression={"$size": [[1, 2, 3, {"$size": "$arr"}]]},
        doc={"arr": [1, 2, 3]},
        expected=4,
        msg="$size should count an array containing a nested $size result",
    ),
]

ALL_EXPR_TESTS = LET_TESTS + FIELD_LOOKUP_TESTS + NESTED_OPERATOR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_size_expression(collection, test):
    """Test $size with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
