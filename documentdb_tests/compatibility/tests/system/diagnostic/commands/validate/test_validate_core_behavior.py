"""Tests for validate command core behavior.

Validates basic functionality, counts, consistency across calls, and comment parameter.
"""

from __future__ import annotations

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import NAMESPACE_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq


def test_validate_populated_collection(collection):
    """Test validate on a populated collection returns valid: true with correct counts."""
    collection.insert_many([{"_id": i, "x": i} for i in range(5)])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nrecords": 5},
        msg="validate should return valid: true with correct nrecords for a populated collection",
    )


def test_validate_empty_collection(database_client, collection):
    """Test validate on an empty collection returns nrecords: 0, valid: true."""
    coll_name = f"{collection.name}_empty"
    database_client.create_collection(coll_name)
    coll = database_client[coll_name]
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nrecords": 0, "nIndexes": 1},
        msg="validate should return nrecords: 0 and nIndexes: 1 for an empty collection",
    )


def test_validate_non_existent_collection(collection):
    """Test validate on a non-existent collection returns NamespaceNotFound error."""
    result = execute_command(collection, {"validate": f"{collection.name}_nonexistent_xyz"})
    assertFailureCode(
        result,
        NAMESPACE_NOT_FOUND_ERROR,
        msg="validate should return NamespaceNotFound for a non-existent collection",
    )


def test_validate_after_insert_and_delete_all(collection):
    """Test validate after inserting and deleting all documents shows nrecords: 0."""
    collection.insert_many([{"_id": i} for i in range(5)])
    collection.delete_many({})
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nrecords": 0},
        msg="validate should return nrecords: 0 after deleting all documents",
    )


def test_validate_consistent_across_calls(collection):
    """Test validate returns consistent results across multiple calls."""
    collection.insert_many([{"_id": i, "x": i} for i in range(5)])
    result1 = execute_command(collection, {"validate": collection.name})
    result2 = execute_command(collection, {"validate": collection.name})
    assertProperties(
        result1,
        {
            "nrecords": Eq(result2["nrecords"]),
            "nIndexes": Eq(result2["nIndexes"]),
            "valid": Eq(result2["valid"]),
        },
        raw_res=True,
        msg="validate should return identical key fields across consecutive calls",
    )


def test_validate_reflects_modifications(collection):
    """Test validate reflects modifications between calls."""
    collection.insert_many([{"_id": i} for i in range(3)])
    execute_command(collection, {"validate": collection.name})
    collection.insert_many([{"_id": i} for i in range(3, 8)])
    result2 = execute_command(collection, {"validate": collection.name})
    assertProperties(
        result2,
        {"nrecords": Eq(8)},
        raw_res=True,
        msg="validate should reflect updated nrecords after additional inserts",
    )


def test_validate_after_dropping_indexes(collection):
    """Test validate after dropping secondary indexes shows nIndexes: 1."""
    collection.insert_one({"_id": 1, "x": 1})
    collection.create_index("x")
    collection.drop_indexes()
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "nIndexes": 1},
        msg="validate should return nIndexes: 1 after dropping secondary indexes",
    )


def test_validate_with_comment(collection):
    """Test validate accepts the comment parameter."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, "comment": "test comment"},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="validate with comment parameter should succeed",
    )
