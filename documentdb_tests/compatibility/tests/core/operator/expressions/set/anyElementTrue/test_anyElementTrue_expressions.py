"""
Tests for $anyElementTrue expression type coverage and field lookup.

Covers literal, field path, nested field path, expression operator input,
system variables, $let variables, composite array paths, and array index paths.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR


# ---------------------------------------------------------------------------
# Expression type smoke tests
# ---------------------------------------------------------------------------
def test_anyElementTrue_literal(collection):
    """Test $anyElementTrue with literal array."""
    result = execute_expression(collection, {"$anyElementTrue": [[True, False]]})
    assert_expression_result(result, expected=True, msg="Literal array should work")


def test_anyElementTrue_field_path(collection):
    """Test $anyElementTrue with field path."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$arr"]}, {"arr": [True, False]}
    )
    assert_expression_result(result, expected=True, msg="Field path should work")


def test_anyElementTrue_nested_field_path(collection):
    """Test $anyElementTrue with nested field path."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$a.b"]}, {"a": {"b": [True, False]}}
    )
    assert_expression_result(result, expected=True, msg="Nested field path should work")


def test_anyElementTrue_expression_operator(collection):
    """Test $anyElementTrue with expression operator as argument."""
    result = execute_expression(
        collection, {"$anyElementTrue": [{"$concatArrays": [[True], [False]]}]}
    )
    assert_expression_result(result, expected=True, msg="Expression operator argument should work")


def test_anyElementTrue_system_var_root(collection):
    """Test $anyElementTrue with $$ROOT.arr system variable."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$$ROOT.arr"]}, {"arr": [True]}
    )
    assert_expression_result(
        result, expected=True, msg="Should handle ROOT variable with field path"
    )


def test_anyElementTrue_system_var_current(collection):
    """Test $anyElementTrue with $$CURRENT.arr system variable."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$$CURRENT.arr"]}, {"arr": [True]}
    )
    assert_expression_result(
        result, expected=True, msg="Should handle CURRENT variable with field path"
    )


def test_anyElementTrue_let_variable(collection):
    """Test $anyElementTrue with $let variable."""
    result = execute_expression(
        collection, {"$let": {"vars": {"x": [True, False]}, "in": {"$anyElementTrue": ["$$x"]}}}
    )
    assert_expression_result(result, expected=True, msg="Should handle let variable input")


# ---------------------------------------------------------------------------
# Field lookup coverage
# ---------------------------------------------------------------------------
def test_anyElementTrue_simple_field(collection):
    """Test $anyElementTrue with simple field lookup."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$arr"]}, {"arr": [1]})
    assert_expression_result(result, expected=True, msg="Simple field should work")


def test_anyElementTrue_nested_field(collection):
    """Test $anyElementTrue with nested object field lookup."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$a.b"]}, {"a": {"b": [1]}}
    )
    assert_expression_result(result, expected=True, msg="Nested field should work")


def test_anyElementTrue_nonexistent_field(collection):
    """Test $anyElementTrue with non-existent field."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$nonexistent"]}, {"x": 1}
    )
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Non-existent field should error"
    )


def test_anyElementTrue_composite_array_path(collection):
    """Test $anyElementTrue with composite array path."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$a.b"]}, {"a": [{"b": [1]}, {"b": [2]}]}
    )
    assert_expression_result(
        result, expected=True, msg="Should return true for composite array path"
    )


def test_anyElementTrue_array_index_path(collection):
    """Test $anyElementTrue with array index path in expression context."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$a.0"]}, {"a": [[1, 2], [3, 4]]}
    )
    assert_expression_result(
        result,
        expected=False,
        msg="Should return false for array index path resolving to empty array",
    )
