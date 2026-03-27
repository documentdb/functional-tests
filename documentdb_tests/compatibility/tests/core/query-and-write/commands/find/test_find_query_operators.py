"""
Query operator tests for find operations.

Tests for comparison operators: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
"""

import pytest

from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.assertions import assertSuccess


@pytest.mark.find
def test_find_gt_operator(collection):
    """Test find with $gt (greater than) operator."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25},
        {"_id": 2, "a": "C", "b": 35},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$gt": 25}}})
    
    expected = [
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 2, "a": "C", "b": 35}
    ]
    assertSuccess(result, expected, "Should match documents with b > 25")


@pytest.mark.find
def test_find_gte_operator(collection):
    """Test find with $gte (greater than or equal) operator."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25},
        {"_id": 2, "a": "C", "b": 35},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$gte": 30}}})
    
    expected = [
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 2, "a": "C", "b": 35}
    ]
    assertSuccess(result, expected, "Should match documents with b >= 30")


@pytest.mark.find
def test_find_lt_operator(collection):
    """Test find with $lt (less than) operator."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25},
        {"_id": 2, "a": "C", "b": 35},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$lt": 30}}})
    
    expected = [{"_id": 1, "a": "B", "b": 25}]
    assertSuccess(result, expected, "Should match documents with b < 30")


@pytest.mark.find
def test_find_lte_operator(collection):
    """Test find with $lte (less than or equal) operator."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25},
        {"_id": 2, "a": "C", "b": 35},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$lte": 30}}})
    
    expected = [
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25}
    ]
    assertSuccess(result, expected, "Should match documents with b <= 30")


@pytest.mark.find
def test_find_ne_operator(collection):
    """Test find with $ne (not equal) operator."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25},
        {"_id": 2, "a": "C", "b": 35},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$ne": 30}}})
    
    expected = [
        {"_id": 1, "a": "B", "b": 25},
        {"_id": 2, "a": "C", "b": 35}
    ]
    assertSuccess(result, expected, "Should match documents with b != 30")


@pytest.mark.find
def test_find_in_operator(collection):
    """Test find with $in operator."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": "active"},
        {"_id": 1, "a": "B", "b": "inactive"},
        {"_id": 2, "a": "C", "b": "pending"},
        {"_id": 3, "a": "D", "b": "active"},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$in": ["active", "pending"]}}})
    
    expected = [
        {"_id": 0, "a": "A", "b": "active"},
        {"_id": 2, "a": "C", "b": "pending"},
        {"_id": 3, "a": "D", "b": "active"}
    ]
    assertSuccess(result, expected, "Should match documents with b in [active, pending]")


@pytest.mark.find
def test_find_nin_operator(collection):
    """Test find with $nin (not in) operator."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": "active"},
        {"_id": 1, "a": "B", "b": "inactive"},
        {"_id": 2, "a": "C", "b": "pending"},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$nin": ["active", "pending"]}}})
    
    expected = [{"_id": 1, "a": "B", "b": "inactive"}]
    assertSuccess(result, expected, "Should match documents with b not in [active, pending]")


@pytest.mark.find
def test_find_range_query(collection):
    """Test find with range query (combining $gte and $lte)."""
    collection.insert_many([
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25},
        {"_id": 2, "a": "C", "b": 35},
    ])
    result = execute_command(collection, {"find": collection.name, "filter": {"b": {"$gte": 25, "$lte": 30}}})
    
    expected = [
        {"_id": 0, "a": "A", "b": 30},
        {"_id": 1, "a": "B", "b": 25}
    ]
    assertSuccess(result, expected, "Should match documents with 25 <= b <= 30")
