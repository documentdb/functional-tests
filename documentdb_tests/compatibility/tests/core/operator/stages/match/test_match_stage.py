"""
Aggregation $match stage tests.

Tests for the $match stage in aggregation pipelines.
"""

import pytest


@pytest.mark.aggregate
@pytest.mark.smoke
def test_match_simple_filter(collection):
    """Test $match stage with simple equality filter."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30, "status": "active"},
        {"name": "Bob", "age": 25, "status": "active"},
        {"name": "Charlie", "age": 35, "status": "inactive"},
    ])

    # Act - Execute aggregation with $match stage
    pipeline = [{"$match": {"status": "active"}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 active users"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Bob"}, "Expected Alice and Bob"


@pytest.mark.aggregate
def test_match_with_comparison_operator(collection):
    """Test $match stage with comparison operators."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ])

    # Act - Execute aggregation with $match using $gt
    pipeline = [{"$match": {"age": {"$gt": 25}}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 users with age > 25"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Charlie"}, "Expected Alice and Charlie"


@pytest.mark.aggregate
def test_match_multiple_conditions(collection):
    """Test $match stage with multiple filter conditions."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "SF"},
        {"name": "Charlie", "age": 35, "city": "NYC"},
    ])

    # Act - Execute aggregation with multiple conditions in $match
    pipeline = [{"$match": {"city": "NYC", "age": {"$gte": 30}}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 users from NYC with age >= 30"
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Charlie"}, "Expected Alice and Charlie"


@pytest.mark.aggregate
@pytest.mark.find
def test_match_empty_result(collection):
    """Test $match stage that matches no documents."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "status": "active"},
        {"name": "Bob", "status": "active"},
    ])

    # Act - Execute aggregation with $match that matches nothing
    pipeline = [{"$match": {"status": "inactive"}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify empty result
    assert result == [], "Expected empty result when no documents match"
