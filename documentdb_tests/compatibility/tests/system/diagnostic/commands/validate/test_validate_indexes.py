"""Tests for validate command with various index types.

Validates that validate succeeds and correctly reports on collections with
different index types including unique, sparse, TTL, text, 2dsphere, hashed,
wildcard, compound, and partial filter indexes.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Index Types]: validate succeeds and reports correct nIndexes for
# collections with various index types.
INDEX_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "unique_index",
        setup=[
            {"insert": "", "documents": [{"_id": i, "x": i} for i in range(5)]},
            {
                "createIndexes": "",
                "indexes": [{"key": {"x": 1}, "name": "x_1", "unique": True}],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nIndexes": Eq(2)},
        msg="validate should succeed and report unique index",
    ),
    DiagnosticTestCase(
        "sparse_index",
        setup=[
            {
                "insert": "",
                "documents": [{"_id": i, "x": i} for i in range(5)]
                + [{"_id": i} for i in range(5, 10)],
            },
            {
                "createIndexes": "",
                "indexes": [{"key": {"x": 1}, "name": "x_1_sparse", "sparse": True}],
            },
        ],
        checks={
            "ok": Eq(1.0),
            "valid": Eq(True),
            "nrecords": Eq(10),
            "nIndexes": Eq(2),
        },
        msg="validate should succeed with sparse index",
    ),
    DiagnosticTestCase(
        "ttl_index",
        setup=[
            {
                "insert": "",
                "documents": [
                    {
                        "_id": 1,
                        "created": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    }
                ],
            },
            {
                "createIndexes": "",
                "indexes": [
                    {
                        "key": {"created": 1},
                        "name": "created_ttl",
                        "expireAfterSeconds": 3600,
                    }
                ],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nIndexes": Eq(2)},
        msg="validate should succeed and report TTL index",
    ),
    DiagnosticTestCase(
        "text_index",
        setup=[
            {
                "insert": "",
                "documents": [{"_id": i, "content": f"document text {i}"} for i in range(5)],
            },
            {
                "createIndexes": "",
                "indexes": [{"key": {"content": "text"}, "name": "content_text"}],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True)},
        msg="validate should succeed with text index",
    ),
    DiagnosticTestCase(
        "2dsphere_index",
        setup=[
            {
                "insert": "",
                "documents": [
                    {
                        "_id": 1,
                        "location": {
                            "type": "Point",
                            "coordinates": [0.0, 0.0],
                        },
                    }
                ],
            },
            {
                "createIndexes": "",
                "indexes": [{"key": {"location": "2dsphere"}, "name": "location_2dsphere"}],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True)},
        msg="validate should succeed with 2dsphere index",
    ),
    DiagnosticTestCase(
        "hashed_index",
        setup=[
            {"insert": "", "documents": [{"_id": i, "x": i} for i in range(5)]},
            {
                "createIndexes": "",
                "indexes": [{"key": {"x": "hashed"}, "name": "x_hashed"}],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nIndexes": Eq(2)},
        msg="validate should succeed with hashed index",
    ),
    DiagnosticTestCase(
        "wildcard_index",
        setup=[
            {
                "insert": "",
                "documents": [{"_id": i, "a": i, "b": str(i)} for i in range(5)],
            },
            {
                "createIndexes": "",
                "indexes": [{"key": {"$**": 1}, "name": "wildcard"}],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True)},
        msg="validate should succeed with wildcard index",
    ),
    DiagnosticTestCase(
        "compound_index",
        setup=[
            {
                "insert": "",
                "documents": [{"_id": i, "a": i, "b": -i} for i in range(5)],
            },
            {
                "createIndexes": "",
                "indexes": [{"key": {"a": 1, "b": -1}, "name": "a_1_b_neg1"}],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nIndexes": Eq(2)},
        msg="validate should succeed and report compound index",
    ),
    DiagnosticTestCase(
        "partial_filter_index",
        setup=[
            {"insert": "", "documents": [{"_id": i, "x": i} for i in range(10)]},
            {
                "createIndexes": "",
                "indexes": [
                    {
                        "key": {"x": 1},
                        "name": "x_partial",
                        "partialFilterExpression": {"x": {"$gt": 4}},
                    }
                ],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nIndexes": Eq(2)},
        msg="validate should succeed with partial filter index",
    ),
    DiagnosticTestCase(
        "multiple_indexes",
        setup=[
            {
                "insert": "",
                "documents": [{"_id": i, "a": i, "b": str(i)} for i in range(5)],
            },
            {
                "createIndexes": "",
                "indexes": [
                    {"key": {"a": 1}, "name": "a_unique", "unique": True},
                    {"key": {"b": 1}, "name": "b_1"},
                    {"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},
                ],
            },
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nIndexes": Eq(4)},
        msg="validate should report all 4 indexes (_id + 3 secondary)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INDEX_TYPE_TESTS))
def test_validate_index_types(collection, test):
    """Test validate with various index types."""
    for cmd in test.setup:
        execute_command(collection, {**cmd, next(iter(cmd)): collection.name})
    result = execute_command(collection, {"validate": collection.name})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
