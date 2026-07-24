"""
Expression and field path tests for $slice expression.

Tests nested expressions, field path lookups, and composite paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Nested Expression]: $slice can consume the output of a nested $slice.
NESTED_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_slice_2_level",
        expression={"$slice": [{"$slice": [[1, 2, 3, 4, 5], 4]}, -2]},
        expected=[3, 4],
        msg="$slice should slice the output of a nested $slice",
    ),
    ExpressionTestCase(
        "nested_slice_3_level",
        expression={"$slice": [{"$slice": [{"$slice": [[1, 2, 3, 4, 5, 6, 7], 5]}, -4]}, 2]},
        expected=[2, 3],
        msg="$slice should slice through three nested $slice levels",
    ),
]

# Property [Field Path Input]: $slice resolves a field path to the array argument.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        expression={"$slice": ["$a.b", 2]},
        doc={"a": {"b": [10, 20, 30]}},
        expected=[10, 20],
        msg="$slice should resolve a nested field path",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$slice": ["$a.b.c", -2]},
        doc={"a": {"b": {"c": [5, 6, 7, 8]}}},
        expected=[7, 8],
        msg="$slice should resolve a deeply nested field path",
    ),
    ExpressionTestCase(
        "composite_array_path",
        expression={"$slice": ["$a.b", 2]},
        doc={"a": [{"b": 10}, {"b": 20}, {"b": 30}]},
        expected=[10, 20],
        msg="$slice should resolve a composite array path",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_EXPR_TESTS))
def test_slice_nested_expression(collection, test):
    """Test $slice composed with other expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(FIELD_LOOKUP_TESTS))
def test_slice_field_lookup(collection, test):
    """Test $slice with field path lookups from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
