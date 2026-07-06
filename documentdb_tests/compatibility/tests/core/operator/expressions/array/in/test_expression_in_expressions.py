"""
Expression and field path tests for $in expression.

Tests nested expressions, field path lookups, composite paths,
and non-existent field handling.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import EXPRESSION_IN_NOT_ARRAY_ERROR


# Nested expressions
@pytest.mark.parametrize(
    "expression,expected",
    [
        # Nested $in: result of inner $in used as search value in outer $in
        ({"$in": [{"$in": [2, [1, 2, 3]]}, [True, False]]}, True),
    ],
    ids=["nested_in_in"],
)
def test_in_nested_expression(collection, expression, expected):
    """Test $in composed with other expressions."""
    result = execute_expression(collection, expression)
    assert_expression_result(result, expected=expected)


# Field path lookups
@pytest.mark.parametrize(
    "document,value,array_ref,expected",
    [
        ({"a": {"b": [10, 20, 30]}}, 20, "$a.b", True),
        ({"a": {"b": [10, 20, 30]}}, 99, "$a.b", False),
        ({"a": {"b": {"c": [5, 6, 7]}}}, 7, "$a.b.c", True),
    ],
    ids=["nested_field_found", "nested_field_not_found", "deeply_nested_field"],
)
def test_in_field_lookup(collection, document, value, array_ref, expected):
    """Test $in with field path lookups from inserted documents."""
    result = execute_expression_with_insert(collection, {"$in": [value, array_ref]}, document)
    assert_expression_result(result, expected=expected)


# Non-existent field as array → error (missing resolves to non-array)
def test_in_nonexistent_array_field(collection):
    """Test $in where array field does not exist (resolves to missing)."""
    result = execute_expression_with_insert(collection, {"$in": [1, "$nonexistent"]}, {"other": 1})
    assert_expression_result(result, error_code=EXPRESSION_IN_NOT_ARRAY_ERROR)


# Non-existent field as value (resolves to missing/null)
@pytest.mark.parametrize(
    "document,expected",
    [
        ({"arr": [1, None, 3]}, False),
        ({"arr": [1, 2, 3]}, False),
    ],
    ids=["array_contains_null", "array_without_null"],
)
def test_in_nonexistent_value_field(collection, document, expected):
    """Test $in where value field does not exist (missing vs null)."""
    result = execute_expression_with_insert(collection, {"$in": ["$nonexistent", "$arr"]}, document)
    assert_expression_result(result, expected=expected)


def test_in_composite_array_as_array(collection):
    """Test $in with composite array from $x.y as the array argument."""
    result = execute_expression_with_insert(
        collection, {"$in": [20, "$x.y"]}, {"x": [{"y": 10}, {"y": 20}, {"y": 30}]}
    )
    assert_expression_result(result, expected=True)


def test_in_composite_array_as_value(collection):
    """Test $in with composite array from $x.y as the search value."""
    result = execute_expression_with_insert(
        collection,
        {"$in": ["$x.y", [[10, 20, 30], "other"]]},
        {"x": [{"y": 10}, {"y": 20}, {"y": 30}]},
    )
    assert_expression_result(result, expected=True)
