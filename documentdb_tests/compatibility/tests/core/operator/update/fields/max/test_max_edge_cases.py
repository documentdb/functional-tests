"""
Edge case tests for $max update field operator.

Tests $max with indexed fields and large documents.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_max_on_indexed_field(collection):
    """Test $max on indexed field → index updated correctly."""
    execute_command(collection, {"insert": collection.name, "documents": [{"_id": 1, "val": 10}]})
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"val": 1}, "name": "val_idx"}]},
    )
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"val": 50}}}]},
    )
    # Verify via index scan
    result = execute_command(collection, {"find": collection.name, "filter": {"val": 50}})
    assertSuccess(result, [{"_id": 1, "val": 50}], "Index should reflect updated value")


def test_max_on_compound_index_field(collection):
    """Test $max on field that is part of a compound index."""
    execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": 1, "a": 10, "b": 20}]}
    )
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "compound_ab"}],
        },
    )
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"a": 50}}}]},
    )
    # Verify via compound index query
    result = execute_command(collection, {"find": collection.name, "filter": {"a": 50, "b": 20}})
    assertSuccess(
        result, [{"_id": 1, "a": 50, "b": 20}], "Compound index should reflect updated field value"
    )


def test_max_large_document_near_bson_limit(collection):
    """Test $max on a document approaching 16MB BSON limit."""
    # Create a document with a large string field (~1MB)
    large_value = "x" * (1024 * 1024)
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "data": large_value, "val": 10}]},
    )
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"val": 99}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "projection": {"val": 1}}
    )
    assertSuccess(
        result, [{"_id": 1, "val": 99}], "$max should work on large documents near BSON limit"
    )
