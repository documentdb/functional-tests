"""
Tests for $allElementsTrue with large arrays.

Covers scale testing with 1000+ element arrays,
falsy at different positions, and heavy duplication.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)


def test_allElementsTrue_large_all_truthy(collection):
    """Test $allElementsTrue with 1000 ones returns true."""
    result = execute_expression(collection, {"$allElementsTrue": [[1] * 1000]})
    assert_expression_result(result, expected=True, msg="1000 ones should return true")


def test_allElementsTrue_large_falsy_at_end(collection):
    """Test $allElementsTrue with 999 ones followed by 0 returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[1] * 999 + [0]]})
    assert_expression_result(result, expected=False, msg="Single falsy at end should return false")


def test_allElementsTrue_large_falsy_at_start(collection):
    """Test $allElementsTrue with 0 followed by 999 ones returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[0] + [1] * 999]})
    assert_expression_result(
        result, expected=False, msg="Single falsy at start should return false"
    )


def test_allElementsTrue_large_falsy_at_middle(collection):
    """Test $allElementsTrue with falsy at index 500 of 1000-element array."""
    result = execute_expression(collection, {"$allElementsTrue": [[1] * 500 + [0] + [1] * 499]})
    assert_expression_result(
        result, expected=False, msg="Single falsy at middle should return false"
    )


def test_allElementsTrue_large_all_falsy(collection):
    """Test $allElementsTrue with 1000 zeros returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[0] * 1000]})
    assert_expression_result(result, expected=False, msg="1000 zeros should return false")


def test_allElementsTrue_large_range(collection):
    """Test $allElementsTrue with array [0..999] returns false (contains zero)."""
    result = execute_expression(collection, {"$allElementsTrue": [list(range(1000))]})
    assert_expression_result(
        result, expected=False, msg="Should return false for range containing zero"
    )


def test_allElementsTrue_large_range_no_zero(collection):
    """Test $allElementsTrue with array [1..1000] returns true."""
    result = execute_expression(collection, {"$allElementsTrue": [list(range(1, 1001))]})
    assert_expression_result(result, expected=True, msg="Should return true for range without zero")


def test_allElementsTrue_scale_10k(collection):
    """Test $allElementsTrue with 10000-element all-truthy array."""
    result = execute_expression(collection, {"$allElementsTrue": [list(range(1, 10001))]})
    assert_expression_result(
        result, expected=True, msg="Should return true for 10000 non-zero elements"
    )


def test_allElementsTrue_scale_10k_last_falsy(collection):
    """Test $allElementsTrue with 10000 elements, last is falsy."""
    result = execute_expression(collection, {"$allElementsTrue": [[1] * 9999 + [0]]})
    assert_expression_result(
        result, expected=False, msg="10000 elements with last falsy should return false"
    )
