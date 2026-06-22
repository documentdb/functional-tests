"""Tests for validate command edge cases.

Validates behavior with collection name edge cases, document variety, and
large collections.
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


def test_validate_long_collection_name(database_client, collection):
    """Test validate with a very long collection name succeeds."""
    db_name = database_client.name
    # Namespace is "db.coll" so max coll length is 255 - len(db_name) - 1.
    max_coll_len = 255 - len(db_name) - 1
    coll_name = f"{collection.name}_" + "a" * (max_coll_len - len(collection.name) - 1)
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="validate should succeed with a long collection name"
    )


def test_validate_unicode_collection_name(database_client, collection):
    """Test validate with unicode characters in collection name succeeds."""
    # U+00E9 e-acute, U+00E8 e-grave, U+00EA e-circumflex.
    coll_name = f"{collection.name}_\u00e9\u00e8\u00ea"
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="validate should succeed with unicode collection name"
    )


def test_validate_numeric_looking_collection_name(database_client, collection):
    """Test validate with a numeric-looking collection name succeeds."""
    coll_name = f"{collection.name}_12345"
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="validate should succeed with numeric-looking collection name"
    )


def test_validate_large_document_count(collection):
    """Test validate with 1_000 documents reports correct nrecords."""
    collection.insert_many([{"_id": i, "x": i} for i in range(1_000)])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nrecords": 1_000},
        msg="validate should report correct nrecords for large document count",
    )


def test_validate_document_with_all_bson_types(collection):
    """Test validate on a collection with a document containing all BSON types."""
    collection.insert_one(
        {
            "_id": 1,
            "double_val": 3.14,
            "string_val": "hello",
            "object_val": {"nested": 1},
            "array_val": [1, 2, 3],
            "binary_val": Binary(b"data"),
            "objectid_val": ObjectId(),
            "bool_val": True,
            "date_val": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "null_val": None,
            "regex_val": Regex("test"),
            "int32_val": 42,
            "timestamp_val": Timestamp(1, 1),
            "int64_val": Int64(123_456_789),
            "decimal128_val": Decimal128("1.23"),
            "minkey_val": MinKey(),
            "maxkey_val": MaxKey(),
        }
    )
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True},
        msg="validate should return valid: true for a document with all BSON types",
    )


def test_validate_deeply_nested_document(collection):
    """Test validate on a collection with a deeply nested document."""
    doc = {"_id": 1}
    nested = doc
    for i in range(10):
        nested[f"level_{i}"] = {}
        nested = nested[f"level_{i}"]
    nested["value"] = "deep"
    collection.insert_one(doc)
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True},
        msg="validate should return valid: true for a deeply nested document",
    )


def test_validate_documents_with_arrays(collection):
    """Test validate on a collection with documents containing arrays."""
    collection.insert_many(
        [
            {"_id": 1, "arr": []},
            {"_id": 2, "arr": [1, 2, 3]},
            {"_id": 3, "arr": list(range(100))},
        ]
    )
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nrecords": 3},
        msg="validate should return valid: true for documents with arrays",
    )


def test_validate_documents_with_binary_data(collection):
    """Test validate on a collection with documents containing Binary fields."""
    collection.insert_many(
        [
            {"_id": 1, "data": Binary(b"small")},
            {"_id": 2, "data": Binary(b"\x00" * 1_024)},
        ]
    )
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nrecords": 2},
        msg="validate should return valid: true for documents with binary data",
    )


def test_validate_many_indexes(collection):
    """Test validate with 5 secondary indexes reports correct nIndexes."""
    collection.insert_many([{"_id": i, "a": i, "b": i, "c": i, "d": i, "e": i} for i in range(5)])
    collection.create_index("a")
    collection.create_index("b")
    collection.create_index("c")
    collection.create_index("d")
    collection.create_index("e")
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nIndexes": 6},
        msg="validate should report nIndexes: 6 with 5 secondary indexes",
    )
