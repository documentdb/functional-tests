"""Tests for $isNumber with null and missing field inputs — both return false."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)

pytestmark = pytest.mark.aggregate


def test_isNumber_null_literal(collection):
    """Test $isNumber returns false for a null literal."""
    result = execute_expression(collection, {"$isNumber": None})
    assert_expression_result(result, expected=False, msg="Should return false for null")


def test_isNumber_null_field(collection):
    """Test $isNumber returns false when referencing a document field with a null value."""
    result = execute_expression_with_insert(collection, {"$isNumber": "$value"}, {"value": None})
    assert_expression_result(
        result, expected=False, msg="Should return false for null-valued field"
    )


def test_isNumber_missing_field(collection):
    """Test $isNumber returns false when referencing a field that does not exist in the document."""
    result = execute_expression_with_insert(collection, {"$isNumber": "$value"}, {})
    assert_expression_result(result, expected=False, msg="Should return false for missing field")


def test_isNumber_nested_missing_field(collection):
    """Test $isNumber returns false when referencing a nested field path that does not exist."""
    result = execute_expression_with_insert(collection, {"$isNumber": "$a.b"}, {"a": {}})
    assert_expression_result(
        result, expected=False, msg="Should return false for missing nested field"
    )
