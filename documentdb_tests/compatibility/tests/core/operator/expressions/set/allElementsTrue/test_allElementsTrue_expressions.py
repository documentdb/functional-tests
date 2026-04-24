"""
Tests for $allElementsTrue expression types and field lookups.

Covers literal/field/expression operator/array expression/composite array inputs
and field path resolution.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR


def test_allElementsTrue_literal(collection):
    """Test $allElementsTrue with literal array expression."""
    result = execute_expression(collection, {"$allElementsTrue": [[True, 1]]})
    assert_expression_result(
        result, expected=True, msg="Should return true for literal truthy array"
    )


def test_allElementsTrue_field_path_true(collection):
    """Test $allElementsTrue with field path resolving to all-truthy array."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$arr"]}, {"arr": [True, 1]}
    )
    assert_expression_result(
        result, expected=True, msg="Should return true for field with all truthy values"
    )


def test_allElementsTrue_field_path_false(collection):
    """Test $allElementsTrue with field path resolving to mixed array."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$arr"]}, {"arr": [True, False]}
    )
    assert_expression_result(
        result, expected=False, msg="Should return false for field with mixed truthy and falsy"
    )


def test_allElementsTrue_nested_field_path(collection):
    """Test $allElementsTrue with nested field path."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$a.b"]}, {"a": {"b": [True, 1]}}
    )
    assert_expression_result(result, expected=True, msg="Nested field path should work")


def test_allElementsTrue_expression_operator_input(collection):
    """Test $allElementsTrue with expression operator ($literal) as input."""
    result = execute_expression(collection, {"$allElementsTrue": [{"$literal": [True, 1]}]})
    assert_expression_result(result, expected=True, msg="Should handle literal expression input")


def test_allElementsTrue_array_expression_input_truthy(collection):
    """Test $allElementsTrue with array expression input — fields resolve to truthy."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": [["$x", "$y"]]}, {"x": True, "y": 1}
    )
    assert_expression_result(
        result, expected=True, msg="Array expression with truthy fields should return true"
    )


def test_allElementsTrue_array_expression_input_falsy(collection):
    """Test $allElementsTrue with array expression input — one field resolves to falsy."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": [["$x", "$y"]]}, {"x": True, "y": 0}
    )
    assert_expression_result(
        result, expected=False, msg="Array expression with falsy field should return false"
    )


def test_allElementsTrue_object_expression_input_error(collection):
    """Test $allElementsTrue with object expression input errors (not array)."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": [{"a": "$x"}]}, {"x": 1}
    )
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Object expression should error"
    )


def test_allElementsTrue_composite_array_path_false(collection):
    """Test $allElementsTrue with composite array path resolving to [true, false]."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$a.b"]}, {"a": [{"b": True}, {"b": False}]}
    )
    assert_expression_result(
        result,
        expected=False,
        msg="Should return false for composite path with mixed truthy and falsy",
    )


def test_allElementsTrue_composite_array_path_true(collection):
    """Test $allElementsTrue with composite array path resolving to [true, 1]."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$a.b"]}, {"a": [{"b": True}, {"b": 1}]}
    )
    assert_expression_result(
        result, expected=True, msg="Should return true for composite path with all truthy values"
    )


# ---------------------------------------------------------------------------
# Field lookup patterns
# ---------------------------------------------------------------------------
def test_allElementsTrue_simple_field(collection):
    """Test $allElementsTrue with simple field path."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$arr"]}, {"arr": [True]}
    )
    assert_expression_result(result, expected=True, msg="Simple field should work")


def test_allElementsTrue_deep_nested_field(collection):
    """Test $allElementsTrue with deep nested field path."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$a.b.c"]}, {"a": {"b": {"c": [True]}}}
    )
    assert_expression_result(result, expected=True, msg="Deep nested field should work")


def test_allElementsTrue_composite_array_truthy(collection):
    """Test $allElementsTrue with composite array path — all truthy."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$a.b"]}, {"a": [{"b": 1}, {"b": 2}]}
    )
    assert_expression_result(
        result, expected=True, msg="Should return true for composite path with all non-zero values"
    )


def test_allElementsTrue_array_index_path(collection):
    """Test $allElementsTrue with array index path in expression context."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$a.0"]}, {"a": [[True], [False]]}
    )
    # In aggregation expression context, $a.0 on array resolves to []
    assert_expression_result(
        result,
        expected=True,
        msg="Should return true for array index path resolving to empty array",
    )


def test_allElementsTrue_numeric_index_on_object_key(collection):
    """Test $allElementsTrue with numeric index path on object key."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$a.0"]}, {"a": {"0": [True, 1]}}
    )
    assert_expression_result(
        result, expected=True, msg="Numeric index on object key should resolve to the field"
    )


# ---------------------------------------------------------------------------
# Shorthand syntax (without outer array wrapper)
# ---------------------------------------------------------------------------
def test_allElementsTrue_shorthand_field(collection):
    """Test $allElementsTrue shorthand syntax without outer array wrapper."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": "$arr"}, {"arr": [True, 1]}
    )
    assert_expression_result(result, expected=True, msg="Shorthand syntax should work")


def test_allElementsTrue_shorthand_field_falsy(collection):
    """Test $allElementsTrue shorthand syntax with falsy element."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": "$arr"}, {"arr": [True, 0]}
    )
    assert_expression_result(result, expected=False, msg="Shorthand with falsy should return false")


# ---------------------------------------------------------------------------
# $let variable
# ---------------------------------------------------------------------------
def test_allElementsTrue_let_variable(collection):
    """Test $allElementsTrue with $let variable."""
    result = execute_expression(
        collection, {"$let": {"vars": {"x": [True, 1]}, "in": {"$allElementsTrue": ["$$x"]}}}
    )
    assert_expression_result(result, expected=True, msg="Should handle let variable input")
