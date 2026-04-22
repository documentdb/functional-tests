"""
Tests for $anyElementTrue with large arrays.

Covers scale testing with 1000+ element arrays,
truthy at different positions, and heavy duplication.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)


def test_anyElementTrue_large_all_falsy(collection):
    """Test $anyElementTrue with 1000 zeros returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[0] * 1000]})
    assert_expression_result(result, expected=False, msg="1000 zeros should return false")


def test_anyElementTrue_large_truthy_at_end(collection):
    """Test $anyElementTrue with 999 zeros followed by 1 returns true."""
    result = execute_expression(collection, {"$anyElementTrue": [[0] * 999 + [1]]})
    assert_expression_result(result, expected=True, msg="Single truthy at end should return true")


def test_anyElementTrue_large_truthy_at_start(collection):
    """Test $anyElementTrue with 1 followed by 999 zeros returns true."""
    result = execute_expression(collection, {"$anyElementTrue": [[1] + [0] * 999]})
    assert_expression_result(result, expected=True, msg="Single truthy at start should return true")


def test_anyElementTrue_large_all_truthy(collection):
    """Test $anyElementTrue with 1000 ones returns true."""
    result = execute_expression(collection, {"$anyElementTrue": [[1] * 1000]})
    assert_expression_result(result, expected=True, msg="1000 ones should return true")


def test_anyElementTrue_large_heavy_duplication(collection):
    """Test $anyElementTrue with 500 nulls and 500 false values returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[None] * 500 + [False] * 500]})
    assert_expression_result(
        result, expected=False, msg="500 nulls + 500 false should return false"
    )


def test_anyElementTrue_large_range(collection):
    """Test $anyElementTrue with array [0..999] returns true (contains non-zero)."""
    result = execute_expression(collection, {"$anyElementTrue": [list(range(1000))]})
    assert_expression_result(
        result, expected=True, msg="Should return true for range containing non-zero values"
    )


def test_anyElementTrue_scale_10k_all_falsy(collection):
    """Test $anyElementTrue with 10000 zeros returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[0] * 10000]})
    assert_expression_result(result, expected=False, msg="10000 zeros should return false")


def test_anyElementTrue_scale_10k_last_truthy(collection):
    """Test $anyElementTrue with 10000 elements, last is truthy."""
    result = execute_expression(collection, {"$anyElementTrue": [[0] * 9999 + [1]]})
    assert_expression_result(
        result, expected=True, msg="10000 elements with last truthy should return true"
    )
