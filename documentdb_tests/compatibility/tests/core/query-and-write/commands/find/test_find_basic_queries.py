"""  
Basic find operation tests.

Tests for fundamental find() and findOne() operations.
"""

import pytest

from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.assertions import assertSuccess, assertFailureCode


@pytest.mark.find
@pytest.mark.smoke
def test_find_all_documents(collection):
    """Test finding all documents in a collection."""
    collection.insert_many([
        {"_id": 0, "a": 1, "b": 1, "c": 1},
        {"_id": 1, "a": 1, "b": 2, "c": 1},
        {"_id": 2, "a": 2, "b": 1, "c": 1},
    ])
    result = execute_command(collection, {"find": collection.name})
    
    expected = [
        {"_id": 0, "a": 1, "b": 1, "c": 1},
        {"_id": 1, "a": 1, "b": 2, "c": 1},
        {"_id": 2, "a": 2, "b": 1, "c": 1},
    ]
    assertSuccess(result, expected, "Should return all 3 documents")


@pytest.mark.find
@pytest.mark.smoke
def test_find_with_filter(collection):
    """Test find operation with a simple equality filter."""
    collection.insert_many([
        {"_id": 0, "a": 1, "b": 1, "c": 1},
        {"_id": 1, "a": 1, "b": 2, "c": 1},
        {"_id": 2, "a": 2, "b": 1, "c": 1},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": 1}})
    
    expected = [
        {"_id": 0, "a": 1, "b": 1, "c": 1},
        {"_id": 2, "a": 2, "b": 1, "c": 1},
    ]
    assertSuccess(result, expected, "Should return only documents with b=1")


@pytest.mark.find
def test_find_one(collection):
    """Test findOne operation returns a single document."""
    collection.insert_many([
        {"_id": 0, "a": 1, "b": 1, "c": 1},
        {"_id": 1, "a": 1, "b": 2, "c": 1},
        {"_id": 2, "a": 2, "b": 1, "c": 1},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": 1}, "limit": 1})
    
    expected = [{"_id": 0, "a": 1, "b": 1, "c": 1}]
    assertSuccess(result, expected, "Should return single document with limit=1")


@pytest.mark.find
def test_find_one_not_found(collection):
    """Test findOne returns None when no document matches."""
    collection.insert_many([
        {"_id": 0, "a": 1, "b": 1, "c": 1},
        {"_id": 1, "a": 1, "b": 2, "c": 1},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"a": 2}, "limit": 1})
    
    assertSuccess(result, [], "Should return empty array when no match")


@pytest.mark.find
def test_find_empty_collection(collection):
    """Test find on an empty collection returns empty result."""
    result = execute_command(collection, {"find": collection.name})
    
    assertSuccess(result, [], "Should return empty array for empty collection")


@pytest.mark.find
def test_find_with_multiple_conditions(collection):
    """Test find with multiple filter conditions (implicit AND)."""
    collection.insert_many([
        {"_id": 0, "a": 1, "b": 1, "c": 1},
        {"_id": 1, "a": 1, "b": 2, "c": 1},
        {"_id": 2, "a": 2, "b": 1, "c": 1},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"a": 1, "b": 2}})
    
    expected = [{"_id": 1, "a": 1, "b": 2, "c": 1}]
    assertSuccess(result, expected, "Should return document matching both conditions")


@pytest.mark.find
def test_find_nested_field(collection):
    """Test find with nested field query using dot notation."""
    collection.insert_many([
        {"_id": 0, "a": 1, "b": {"b1": 1}, "c": 1},
        {"_id": 1, "a": 1, "b": {"b1": 2}, "c": 1},
        {"_id": 2, "a": 2, "b": {"b1": 1}, "c": 1},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b.b1": 1}})
    
    expected = [
        {"_id": 0, "a": 1, "b": {"b1": 1}, "c": 1},
        {"_id": 2, "a": 2, "b": {"b1": 1}, "c": 1}
    ]
    assertSuccess(result, expected, "Should match nested field using dot notation")


@pytest.mark.find
def test_find_invalid_collection(collection):
    """Test find on non-existent collection with invalid name."""
    result = execute_command(collection, {"find": "$invalid"})
    
    assertFailureCode(result, 73, "Should reject invalid collection name")


@pytest.mark.find
def test_find_invalid_filter_type(collection):
    """Test find with non-object filter returns error."""
    result = execute_command(collection, {"find": collection.name, "filter": "invalid"})
    
    assertFailureCode(result, 14, "Should reject non-object filter")
