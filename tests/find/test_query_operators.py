"""
Query operator tests for find operations.

Tests for comparison operators: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
"""

import pytest


@pytest.mark.find
def test_find_gt_operator(collection):
    """Test find with $gt (greater than) operator."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ])

    # Act - Find documents where age > 25
    result = list(collection.find({"age": {"$gt": 25}}))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 documents with age > 25"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Charlie"}, "Expected Alice and Charlie"


@pytest.mark.find
def test_find_gte_operator(collection):
    """Test find with $gte (greater than or equal) operator."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ])

    # Act - Find documents where age >= 30
    result = list(collection.find({"age": {"$gte": 30}}))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 documents with age >= 30"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Charlie"}, "Expected Alice and Charlie"


@pytest.mark.find
def test_find_lt_operator(collection):
    """Test find with $lt (less than) operator."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ])

    # Act - Find documents where age < 30
    result = list(collection.find({"age": {"$lt": 30}}))

    # Assert - Verify results
    assert len(result) == 1, "Expected 1 document with age < 30"
    assert result[0]["name"] == "Bob", "Expected Bob"


@pytest.mark.find
def test_find_lte_operator(collection):
    """Test find with $lte (less than or equal) operator."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ])

    # Act - Find documents where age <= 30
    result = list(collection.find({"age": {"$lte": 30}}))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 documents with age <= 30"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Bob"}, "Expected Alice and Bob"


@pytest.mark.find
def test_find_ne_operator(collection):
    """Test find with $ne (not equal) operator."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ])

    # Act - Find documents where age != 30
    result = list(collection.find({"age": {"$ne": 30}}))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 documents with age != 30"
    names = {doc["name"] for doc in result}
    assert names == {"Bob", "Charlie"}, "Expected Bob and Charlie"


@pytest.mark.find
def test_find_in_operator(collection):
    """Test find with $in operator."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "status": "active"},
        {"name": "Bob", "status": "inactive"},
        {"name": "Charlie", "status": "pending"},
        {"name": "David", "status": "active"},
    ])

    # Act - Find documents where status is in ["active", "pending"]
    result = list(collection.find({"status": {"$in": ["active", "pending"]}}))

    # Assert - Verify results
    assert len(result) == 3, "Expected 3 documents with status in [active, pending]"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Charlie", "David"}, "Expected Alice, Charlie, and David"


@pytest.mark.find
def test_find_nin_operator(collection):
    """Test find with $nin (not in) operator."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "status": "active"},
        {"name": "Bob", "status": "inactive"},
        {"name": "Charlie", "status": "pending"},
    ])

    # Act - Find documents where status is not in ["active", "pending"]
    result = list(collection.find({"status": {"$nin": ["active", "pending"]}}))

    # Assert - Verify results
    assert len(result) == 1, "Expected 1 document with status not in [active, pending]"
    assert result[0]["name"] == "Bob", "Expected Bob"


@pytest.mark.find
@pytest.mark.smoke
def test_find_range_query(collection):
    """Test find with range query (combining $gte and $lte)."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ])

    # Act - Find documents where 25 <= age <= 30
    result = list(collection.find({"age": {"$gte": 25, "$lte": 30}}))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 documents with age between 25 and 30"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Bob"}, "Expected Alice and Bob"
