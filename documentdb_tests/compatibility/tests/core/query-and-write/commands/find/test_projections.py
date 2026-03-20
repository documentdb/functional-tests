"""
Projection tests for find operations.

Tests for field inclusion, exclusion, and projection operators.
"""

import pytest

from documentdb_tests.framework.assertions import assert_field_exists, assert_field_not_exists


@pytest.mark.find
def test_find_with_field_inclusion(collection):
    """Test find with explicit field inclusion."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30, "email": "alice@example.com", "city": "NYC"},
        {"name": "Bob", "age": 25, "email": "bob@example.com", "city": "SF"},
    ])

    # Act - Find with projection to include only name and age
    result = list(collection.find({}, {"name": 1, "age": 1}))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 documents"

    # Verify included fields exist
    for doc in result:
        assert_field_exists(doc, "_id")  # _id is included by default
        assert_field_exists(doc, "name")
        assert_field_exists(doc, "age")

        # Verify excluded fields don't exist
        assert_field_not_exists(doc, "email")
        assert_field_not_exists(doc, "city")


@pytest.mark.find
def test_find_with_field_exclusion(collection):
    """Test find with explicit field exclusion."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30, "email": "alice@example.com", "city": "NYC"},
        {"name": "Bob", "age": 25, "email": "bob@example.com", "city": "SF"},
    ])

    # Act - Find with projection to exclude email and city
    result = list(collection.find({}, {"email": 0, "city": 0}))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 documents"

    # Verify included fields exist
    for doc in result:
        assert_field_exists(doc, "_id")
        assert_field_exists(doc, "name")
        assert_field_exists(doc, "age")

        # Verify excluded fields don't exist
        assert_field_not_exists(doc, "email")
        assert_field_not_exists(doc, "city")


@pytest.mark.find
def test_find_exclude_id(collection):
    """Test find with _id exclusion."""
    # Arrange - Insert test data
    collection.insert_one({"name": "Alice", "age": 30, "email": "alice@example.com"})

    # Act - Find with projection to exclude _id
    result = list(collection.find({}, {"_id": 0, "name": 1, "age": 1}))

    # Assert - Verify results
    assert len(result) == 1, "Expected 1 document"

    # Verify _id is excluded
    assert_field_not_exists(result[0], "_id")
    assert_field_exists(result[0], "name")
    assert_field_exists(result[0], "age")


@pytest.mark.find
def test_find_nested_field_projection(collection):
    """Test find with nested field projection."""
    # Arrange - Insert test data
    collection.insert_one({
        "name": "Alice",
        "profile": {"age": 30, "city": "NYC", "email": "alice@example.com"}
    })

    # Act - Find with projection for nested field
    result = list(collection.find({}, {"name": 1, "profile.age": 1}))

    # Assert - Verify results
    assert len(result) == 1, "Expected 1 document"
    assert_field_exists(result[0], "name")
    assert_field_exists(result[0], "profile.age")

    # Verify other nested fields are not included
    assert "city" not in result[0].get("profile", {}), "city should not be in profile"
    assert "email" not in result[0].get("profile", {}), "email should not be in profile"


@pytest.mark.find
@pytest.mark.smoke
def test_find_empty_projection(collection):
    """Test find with empty projection returns all fields."""
    # Arrange - Insert test data
    collection.insert_one({"name": "Alice", "age": 30})

    # Act - Find with empty projection
    result = collection.find_one({}, {})

    # Assert - Verify all fields are present
    assert_field_exists(result, "_id")
    assert_field_exists(result, "name")
    assert_field_exists(result, "age")
