"""
Edge case tests for $max update field operator.

Tests $max with indexed fields, large documents, and special field names.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_max_on_indexed_field(collection):
    """Test $max on indexed field updates the index correctly."""
    execute_command(collection, {"insert": collection.name, "documents": [{"_id": 1, "val": 10}]})
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"val": 1}, "name": "val_idx"}]},
    )
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"val": 50}}}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"val": 50}})
    assertSuccess(result, [{"_id": 1, "val": 50}], "$max should update indexed field correctly")


def test_max_large_document_near_bson_limit(collection):
    """Test $max on a document approaching 16MB BSON limit."""
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


def test_max_with_unicode_field_name(collection):
    """Test $max with unicode emoji characters as field name."""
    execute_command(collection, {"insert": collection.name, "documents": [{"_id": 1, "🎉": 10}]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"🎉": 42}}}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "🎉": 42}], "$max should update field with unicode key")
