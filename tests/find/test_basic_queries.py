"""
Basic find operation tests.

Tests for fundamental find() and findOne() operations.
"""

import pytest

from framework.assertions import assert_document_match


@pytest.mark.find
@pytest.mark.smoke
def test_find_all_documents(collection):
    """Test finding all documents in a collection."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30, "status": "active"},
        {"name": "Bob", "age": 25, "status": "active"},
        {"name": "Charlie", "age": 35, "status": "inactive"},
    ])

    # Act - Execute find operation
    result = list(collection.find())

    # Assert - Verify all documents are returned
    assert len(result) == 3, "Expected to find 3 documents"

    # Verify document content
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Bob", "Charlie"}, "Expected to find all three users"


@pytest.mark.find
@pytest.mark.smoke
def test_find_with_filter(collection):
    """Test find operation with a simple equality filter."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30, "status": "active"},
        {"name": "Bob", "age": 25, "status": "active"},
        {"name": "Charlie", "age": 35, "status": "inactive"},
    ])

    # Act - Execute find with filter
    result = list(collection.find({"status": "active"}))

    # Assert - Verify only active users are returned
    assert len(result) == 2, "Expected to find 2 active users"

    # Verify all returned documents have status "active"
    for doc in result:
        assert doc["status"] == "active", "All returned documents should have status 'active'"

    # Verify correct users are returned
    names = {doc["name"] for doc in result}
    assert names == {"Alice", "Bob"}, "Expected to find Alice and Bob"


@pytest.mark.find
def test_find_one(collection):
    """Test findOne operation returns a single document."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ])

    # Act - Execute findOne
    result = collection.find_one({"name": "Alice"})

    # Assert - Verify document is returned and content matches
    assert result is not None, "Expected to find a document"
    assert_document_match(result, {"name": "Alice", "age": 30})


@pytest.mark.find
def test_find_one_not_found(collection):
    """Test findOne returns None when no document matches."""
    # Arrange - Insert test data
    collection.insert_one({"name": "Alice", "age": 30})

    # Act - Execute findOne with non-matching filter
    result = collection.find_one({"name": "NonExistent"})

    # Assert - Verify None is returned
    assert result is None, "Expected None when no document matches"


@pytest.mark.find
def test_find_empty_collection(collection):
    """Test find on an empty collection returns empty result."""
    # Arrange - Collection is already empty (no insertion needed)

    # Act - Execute find on empty collection
    result = list(collection.find())

    # Assert - Verify empty result
    assert result == [], "Expected empty result for empty collection"


@pytest.mark.find
def test_find_with_multiple_conditions(collection):
    """Test find with multiple filter conditions (implicit AND)."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "SF"},
        {"name": "Charlie", "age": 35, "city": "NYC"},
    ])

    # Act - Execute find with multiple conditions
    result = list(collection.find({"city": "NYC", "age": 30}))

    # Assert - Verify only matching document is returned
    assert len(result) == 1, "Expected to find 1 document"
    assert_document_match(result[0], {"name": "Alice", "age": 30, "city": "NYC"})


@pytest.mark.find
def test_find_nested_field(collection):
    """Test find with nested field query using dot notation."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "profile": {"age": 30, "city": "NYC"}},
        {"name": "Bob", "profile": {"age": 25, "city": "SF"}},
    ])

    # Act - Execute find with nested field
    result = list(collection.find({"profile.city": "NYC"}))

    # Assert - Verify correct document is returned
    assert len(result) == 1, "Expected to find 1 document"
    assert result[0]["name"] == "Alice", "Expected to find Alice"
