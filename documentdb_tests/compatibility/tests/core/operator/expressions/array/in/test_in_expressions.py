"""
Expression and field path tests for $in expression.

Tests nested expressions, field path lookups, composite paths,
and non-existent field handling.
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
from documentdb_tests.framework.error_codes import EXPRESSION_IN_NOT_ARRAY_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Nested Expressions]: $in evaluates nested expressions as arguments.
NESTED_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_in_in",
        expression={"$in": [{"$in": [2, [1, 2, 3]]}, [True, False]]},
        expected=True,
        msg="$in should accept nested $in result as search value",
    ),
]

# Property [Field Path Resolution]: $in resolves nested and deeply nested field paths.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_found",
        expression={"$in": [20, "$a.b"]},
        doc={"a": {"b": [10, 20, 30]}},
        expected=True,
        msg="$in should find value in nested field path array",
    ),
    ExpressionTestCase(
        "nested_field_not_found",
        expression={"$in": [99, "$a.b"]},
        doc={"a": {"b": [10, 20, 30]}},
        expected=False,
        msg="$in should not find absent value in nested field path array",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$in": [7, "$a.b.c"]},
        doc={"a": {"b": {"c": [5, 6, 7]}}},
        expected=True,
        msg="$in should resolve deeply nested field path",
    ),
]

# Property [Missing Field]: $in handles missing array and value fields correctly.
MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nonexistent_array_field",
        expression={"$in": [1, "$nonexistent"]},
        doc={"other": 1},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should error when array field does not exist",
    ),
    ExpressionTestCase(
        "nonexistent_value_array_contains_null",
        expression={"$in": ["$nonexistent", "$arr"]},
        doc={"arr": [1, None, 3]},
        expected=False,
        msg="$in should return false for missing value even when array contains null",
    ),
    ExpressionTestCase(
        "nonexistent_value_array_without_null",
        expression={"$in": ["$nonexistent", "$arr"]},
        doc={"arr": [1, 2, 3]},
        expected=False,
        msg="$in should return false for missing value in array without null",
    ),
]

# Property [Composite Paths]: $in resolves composite array paths from array-of-objects.
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_as_array",
        expression={"$in": [20, "$x.y"]},
        doc={"x": [{"y": 10}, {"y": 20}, {"y": 30}]},
        expected=True,
        msg="$in should find value in composite array path",
    ),
    ExpressionTestCase(
        "composite_array_as_value",
        expression={"$in": ["$x.y", [[10, 20, 30], "other"]]},
        doc={"x": [{"y": 10}, {"y": 20}, {"y": 30}]},
        expected=True,
        msg="$in should match composite array as search value",
    ),
]

ALL_EXPRESSION_TESTS = (
    NESTED_EXPRESSION_TESTS + FIELD_LOOKUP_TESTS + MISSING_FIELD_TESTS + COMPOSITE_PATH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPRESSION_TESTS))
def test_in_expression(collection, test):
    """Test $in with expressions, field paths, and composite paths."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
