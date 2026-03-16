"""
Projection tests for find operations.

Tests for field inclusion, exclusion, and projection operators.
"""

import pytest

from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.assertions import assertSuccess


@pytest.mark.find
def test_find_with_field_inclusion(collection):
    """Test find with explicit field inclusion."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30, "c": "alice@example.com", "d": "NYC"},
        {"_id": 1, "a": "B", "b": 25, "c": "bob@example.com", "d": "SF"},
    ])
    result = execute_command(collection, {"find": collection.name, "projection": {"a": 1, "b": 1}})
    
    expected = [
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25}
    ]
    assertSuccess(result, expected, "Should include only specified fields")


@pytest.mark.find
def test_find_with_field_exclusion(collection):
    """Test find with explicit field exclusion."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30, "c": "alice@example.com", "d": "NYC"},
        {"_id": 1, "a": "B", "b": 25, "c": "bob@example.com", "d": "SF"},
    ])
    result = execute_command(collection, {"find": collection.name, "projection": {"c": 0, "d": 0}})
    
    expected = [
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25}
    ]
    assertSuccess(result, expected, "Should exclude specified fields")


@pytest.mark.find
def test_find_exclude_id(collection):
    """Test find with _id exclusion."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30, "c": "alice@example.com"},
    ])
    result = execute_command(collection, {"find": collection.name, "projection": {"_id": 0, "a": 1, "b": 1}})
    
    expected = [{"a": "A", "b": 30}]
    assertSuccess(result, expected, "Should exclude _id field")


@pytest.mark.find
def test_find_nested_field_projection(collection):
    """Test find with nested field projection."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": {"b1": 30, "b2": "NYC", "b3": "alice@example.com"}},
    ])
    result = execute_command(collection, {"find": collection.name, "projection": {"a": 1, "b.b1": 1}})
    
    expected = [{"_id": 0, "a": "A", "b": {"b1": 30}}]
    assertSuccess(result, expected, "Should project nested field")


@pytest.mark.find
def test_find_empty_projection(collection):
    """Test find with empty projection returns all fields."""
    collection.insert_many([{"_id": 0, "a": "A", "b": 30}])
    result = execute_command(collection, {"find": collection.name, "limit": 1})
    
    expected = [{"_id": 0, "a": "A", "b": 30}]
    assertSuccess(result, expected, "Should return all fields")
