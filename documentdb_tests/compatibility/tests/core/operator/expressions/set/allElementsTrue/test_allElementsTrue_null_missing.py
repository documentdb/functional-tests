"""
Tests for $allElementsTrue null and missing field propagation.

Covers null as array element, null as array argument,
and missing field behavior.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR


# ---------------------------------------------------------------------------
# Null as array element (falsy)
# ---------------------------------------------------------------------------
def test_allElementsTrue_null_sole_element(collection):
    """Test $allElementsTrue with [null] returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[None]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for array with only null"
    )


def test_allElementsTrue_null_null(collection):
    """Test $allElementsTrue with [null, null] returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[None, None]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for array with two nulls"
    )


def test_allElementsTrue_null_true(collection):
    """Test $allElementsTrue with [null, true] returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[None, True]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for null combined with true"
    )


def test_allElementsTrue_null_1(collection):
    """Test $allElementsTrue with [null, 1] returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[None, 1]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for null combined with one"
    )


def test_allElementsTrue_many_nulls(collection):
    """Test $allElementsTrue with 10 nulls returns false."""
    result = execute_expression(collection, {"$allElementsTrue": [[None] * 10]})
    assert_expression_result(result, expected=False, msg="Should return false for ten nulls")


# ---------------------------------------------------------------------------
# Null as array argument (error — not an array)
# ---------------------------------------------------------------------------
def test_allElementsTrue_null_argument(collection):
    """Test $allElementsTrue with null as argument errors."""
    result = execute_expression(collection, {"$allElementsTrue": [None]})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Null argument should error"
    )


# ---------------------------------------------------------------------------
# Missing field as array argument
# ---------------------------------------------------------------------------
def test_allElementsTrue_missing_field_argument(collection):
    """Test $allElementsTrue with missing field as argument errors."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$missing_field"]}, {"x": 1}
    )
    assert_expression_result(
        result,
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Missing field argument should error",
    )
