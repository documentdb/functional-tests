"""
Insert operation tests.

Tests for insertOne, insertMany, and related operations.
"""

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from documentdb_tests.framework.assertions import assert_count


@pytest.mark.insert
@pytest.mark.smoke
def test_insert_one_document(collection):
    """Test inserting a single document."""
    # Insert one document
    document = {"name": "Alice", "age": 30}
    result = collection.insert_one(document)

    # Verify insert was acknowledged
    assert result.acknowledged, "Insert should be acknowledged"
    assert result.inserted_id is not None, "Should return inserted _id"
    assert isinstance(result.inserted_id, ObjectId), "Inserted _id should be ObjectId"

    # Verify document exists in collection
    assert_count(collection, {}, 1)

    # Verify document content
    found = collection.find_one({"name": "Alice"})
    assert found is not None, "Document should exist"
    assert found["name"] == "Alice"
    assert found["age"] == 30


@pytest.mark.insert
@pytest.mark.smoke
def test_insert_many_documents(collection):
    """Test inserting multiple documents."""
    # Insert multiple documents
    documents = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
    ]
    result = collection.insert_many(documents)

    # Verify insert was acknowledged
    assert result.acknowledged, "Insert should be acknowledged"
    assert len(result.inserted_ids) == 3, "Should return 3 inserted IDs"

    # Verify all IDs are ObjectIds
    for inserted_id in result.inserted_ids:
        assert isinstance(inserted_id, ObjectId), "Each inserted _id should be ObjectId"

    # Verify all documents exist
    assert_count(collection, {}, 3)


@pytest.mark.insert
def test_insert_with_custom_id(collection):
    """Test inserting document with custom _id."""
    # Insert document with custom _id
    custom_id = "custom_123"
    document = {"_id": custom_id, "name": "Alice"}
    result = collection.insert_one(document)

    # Verify custom _id is used
    assert result.inserted_id == custom_id, "Should use custom _id"

    # Verify document can be retrieved by custom _id
    found = collection.find_one({"_id": custom_id})
    assert found is not None, "Document should exist"
    assert found["name"] == "Alice"


@pytest.mark.insert
def test_insert_duplicate_id_fails(collection):
    """Test that inserting duplicate _id raises error."""
    # Insert first document
    document = {"_id": "duplicate_id", "name": "Alice"}
    collection.insert_one(document)

    # Try to insert document with same _id
    duplicate = {"_id": "duplicate_id", "name": "Bob"}

    # Should raise DuplicateKeyError
    with pytest.raises(DuplicateKeyError):
        collection.insert_one(duplicate)

    # Verify only first document exists
    assert_count(collection, {}, 1)
    found = collection.find_one({"_id": "duplicate_id"})
    assert found["name"] == "Alice", "Should have first document"


@pytest.mark.insert
def test_insert_nested_document(collection):
    """Test inserting document with nested structure."""
    # Insert document with nested fields
    document = {
        "name": "Alice",
        "profile": {"age": 30, "address": {"city": "NYC", "country": "USA"}},
    }
    result = collection.insert_one(document)

    # Verify insert
    assert result.inserted_id is not None

    # Verify nested structure is preserved
    found = collection.find_one({"name": "Alice"})
    assert found["profile"]["age"] == 30
    assert found["profile"]["address"]["city"] == "NYC"


@pytest.mark.insert
def test_insert_array_field(collection):
    """Test inserting document with array fields."""
    # Insert document with array
    document = {"name": "Alice", "tags": ["python", "mongodb", "testing"], "scores": [95, 87, 92]}
    result = collection.insert_one(document)

    # Verify insert
    assert result.inserted_id is not None

    # Verify array fields are preserved
    found = collection.find_one({"name": "Alice"})
    assert found["tags"] == ["python", "mongodb", "testing"]
    assert found["scores"] == [95, 87, 92]


@pytest.mark.insert
def test_insert_empty_document(collection):
    """Test inserting an empty document."""
    # Insert empty document
    result = collection.insert_one({})

    # Verify insert was successful
    assert result.inserted_id is not None

    # Verify document exists (only has _id)
    found = collection.find_one({"_id": result.inserted_id})
    assert found is not None
    assert len(found) == 1  # Only _id field
    assert "_id" in found
