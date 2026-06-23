"""Tests for validate command edge cases.

Validates behavior with collection name edge cases, document variety, and
large collections.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Document Variety]: validate succeeds for collections with diverse
# document shapes, sizes, and BSON types.
DOCUMENT_VARIETY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "large_document_count",
        setup=[
            {
                "insert": "",
                "documents": [{"_id": i, "x": i} for i in range(1_000)],
            }
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nrecords": Eq(1_000)},
        msg="validate should report correct nrecords for large document count",
    ),
    DiagnosticTestCase(
        "all_bson_types",
        setup=[
            {
                "insert": "",
                "documents": [
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
                ],
            }
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True)},
        msg="validate should return valid: true for a document with all BSON types",
    ),
    DiagnosticTestCase(
        "deeply_nested_document",
        setup=[
            {
                "insert": "",
                "documents": [
                    {
                        "_id": 1,
                        "level_0": {
                            "level_1": {
                                "level_2": {
                                    "level_3": {
                                        "level_4": {
                                            "level_5": {
                                                "level_6": {
                                                    "level_7": {
                                                        "level_8": {"level_9": {"value": "deep"}}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                    }
                ],
            }
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True)},
        msg="validate should return valid: true for a deeply nested document",
    ),
    DiagnosticTestCase(
        "documents_with_arrays",
        setup=[
            {
                "insert": "",
                "documents": [
                    {"_id": 1, "arr": []},
                    {"_id": 2, "arr": [1, 2, 3]},
                    {"_id": 3, "arr": list(range(100))},
                ],
            }
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nrecords": Eq(3)},
        msg="validate should return valid: true for documents with arrays",
    ),
    DiagnosticTestCase(
        "documents_with_binary_data",
        setup=[
            {
                "insert": "",
                "documents": [
                    {"_id": 1, "data": Binary(b"small")},
                    {"_id": 2, "data": Binary(b"\x00" * 1_024)},
                ],
            }
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nrecords": Eq(2)},
        msg="validate should return valid: true for documents with binary data",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOCUMENT_VARIETY_TESTS))
def test_validate_document_variety(collection, test):
    """Test validate with diverse document shapes and index counts."""
    for cmd in test.setup:
        execute_command(collection, {**cmd, next(iter(cmd)): collection.name})
    result = execute_command(collection, {"validate": collection.name})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_validate_unicode_collection_name(database_client, collection):
    """Test validate succeeds with a unicode collection name."""
    coll_name = f"{collection.name}_\u00e9\u00e8\u00ea"
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="validate should succeed with unicode collection name",
    )


def test_validate_numeric_looking_collection_name(database_client, collection):
    """Test validate succeeds with a numeric-looking collection name."""
    coll_name = f"{collection.name}_12345"
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="validate should succeed with numeric-looking collection name",
    )


def test_validate_long_collection_name(database_client, collection):
    """Test validate with a collection name at the max namespace length."""
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
