"""
Tests for $anyElementTrue null and missing field propagation.

Covers null as array element, null as array argument,
and missing field behavior.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR


# ---------------------------------------------------------------------------
# Null as array element (falsy)
# ---------------------------------------------------------------------------
def test_anyElementTrue_null_sole_element(collection):
    """Test $anyElementTrue with [null] returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[None]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for array with only null"
    )


def test_anyElementTrue_null_null(collection):
    """Test $anyElementTrue with [null, null] returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[None, None]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for array with two nulls"
    )


def test_anyElementTrue_null_true(collection):
    """Test $anyElementTrue with [null, true] returns true."""
    result = execute_expression(collection, {"$anyElementTrue": [[None, True]]})
    assert_expression_result(
        result, expected=True, msg="Should return true for null combined with true"
    )


def test_anyElementTrue_null_false(collection):
    """Test $anyElementTrue with [null, false] returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[None, False]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for null combined with false"
    )


def test_anyElementTrue_null_1(collection):
    """Test $anyElementTrue with [null, 1] returns true."""
    result = execute_expression(collection, {"$anyElementTrue": [[None, 1]]})
    assert_expression_result(
        result, expected=True, msg="Should return true for null combined with one"
    )


def test_anyElementTrue_null_0(collection):
    """Test $anyElementTrue with [null, 0] returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[None, 0]]})
    assert_expression_result(
        result, expected=False, msg="Should return false for null combined with zero"
    )


def test_anyElementTrue_many_nulls(collection):
    """Test $anyElementTrue with 10 nulls returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[None] * 10]})
    assert_expression_result(result, expected=False, msg="Should return false for ten nulls")


# ---------------------------------------------------------------------------
# Null as array argument (error — not an array)
# ---------------------------------------------------------------------------
def test_anyElementTrue_null_argument(collection):
    """Test $anyElementTrue with null as argument errors."""
    result = execute_expression(collection, {"$anyElementTrue": [None]})
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Null argument should error"
    )


# ---------------------------------------------------------------------------
# Missing field as array argument
# ---------------------------------------------------------------------------
def test_anyElementTrue_missing_field_argument(collection):
    """Test $anyElementTrue with missing field as argument errors."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$missing_field"]}, {"x": 1}
    )
    assert_expression_result(
        result,
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Missing field argument should error",
    )
