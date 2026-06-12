"""
Insert operation tests.

Tests for insertOne, insertMany, and related operations.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command


@pytest.mark.insert
@pytest.mark.smoke
def test_insert_one_document(collection):
    """Test inserting a single document."""
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": 0, "a": "A", "b": 30}]}
    )

    assertSuccessPartial(result, {"n": 1}, "Should insert one document")


@pytest.mark.insert
@pytest.mark.smoke
def test_insert_many_documents(collection):
    """Test inserting multiple documents."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [
                {"_id": 0, "a": "A", "b": 30},
                {"_id": 1, "a": "B", "b": 25},
                {"_id": 2, "a": "C", "b": 35},
            ],
        },
    )

    assertSuccessPartial(result, {"n": 3}, "Should insert three documents")


@pytest.mark.insert
def test_insert_with_custom_id(collection):
    """Test inserting document with custom _id."""
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": "custom_123", "a": "A"}]}
    )

    assertSuccessPartial(result, {"n": 1}, "Should insert with custom _id")


@pytest.mark.insert
def test_insert_duplicate_id_fails(collection):
    """Test that inserting duplicate _id raises error."""
    execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": "dup", "a": "A"}]}
    )
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": "dup", "a": "B"}]}
    )

    assertFailureCode(result, 11000, "Should reject duplicate _id")


@pytest.mark.insert
def test_insert_nested_document(collection):
    """Test inserting document with nested structure."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 0, "a": "A", "b": {"b1": 30, "b2": {"b3": "NYC"}}}],
        },
    )

    assertSuccessPartial(result, {"n": 1}, "Should insert nested document")


@pytest.mark.insert
def test_insert_array_field(collection):
    """Test inserting document with array fields."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 0, "a": "A", "b": ["python", "mongodb"], "c": [95, 87]}],
        },
    )

    assertSuccessPartial(result, {"n": 1}, "Should insert document with arrays")


@pytest.mark.insert
def test_insert_empty_document(collection):
    """Test inserting an empty document."""
    result = execute_command(collection, {"insert": collection.name, "documents": [{"_id": 0}]})

    assertSuccessPartial(result, {"n": 1}, "Should insert empty document")
