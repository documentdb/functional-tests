"""Tests for collation in bulkWrite operations."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [BulkWrite Update Collation]: individual update operations within a
# bulkWrite can specify collation, affecting filter matching independently.
COLLATION_BULK_UPDATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bulk_update_case_insensitive",
        docs=[
            {"_id": 1, "x": "Apple", "v": 1},
            {"_id": 2, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": {"$set": {"v": 2}},
                    "collation": {"locale": "en", "strength": 2},
                },
                {
                    "q": {"x": "BANANA"},
                    "u": {"$set": {"v": 3}},
                    "collation": {"locale": "en", "strength": 2},
                },
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="bulkWrite updates should each use their own collation",
    ),
    CommandTestCase(
        "bulk_update_mixed_collation",
        docs=[
            {"_id": 1, "x": "Apple", "v": 1},
            {"_id": 2, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": {"$set": {"v": 2}},
                    "collation": {"locale": "en", "strength": 2},
                },
                {
                    "q": {"x": "BANANA"},
                    "u": {"$set": {"v": 3}},
                },
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="bulkWrite with mixed collation: only collated op should match case-insensitively",
    ),
]

# Property [BulkWrite Delete Collation]: individual delete operations within a
# bulkWrite can specify collation, affecting filter matching independently.
COLLATION_BULK_DELETE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bulk_delete_case_insensitive",
        docs=[
            {"_id": 1, "x": "Apple"},
            {"_id": 2, "x": "banana"},
            {"_id": 3, "x": "cherry"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"x": "apple"},
                    "limit": 0,
                    "collation": {"locale": "en", "strength": 2},
                },
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="bulkWrite delete with collation should match case-insensitively",
    ),
    CommandTestCase(
        "bulk_delete_no_collation_binary",
        docs=[
            {"_id": 1, "x": "Apple"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"x": "apple"},
                    "limit": 0,
                },
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="bulkWrite delete without collation should use binary comparison",
    ),
]

# Property [BulkWrite Collection Default Collation]: when no per-operation
# collation is specified, bulkWrite operations inherit the collection default.
COLLATION_BULK_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bulk_update_inherits_collection_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "Apple", "v": 1},
            {"_id": 2, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": {"$set": {"v": 2}},
                },
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="bulkWrite update should inherit collection default collation",
    ),
    CommandTestCase(
        "bulk_delete_inherits_collection_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "Apple"},
            {"_id": 2, "x": "banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"x": "apple"},
                    "limit": 0,
                },
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="bulkWrite delete should inherit collection default collation",
    ),
]

COLLATION_BULK_WRITE_TESTS = (
    COLLATION_BULK_UPDATE_TESTS
    + COLLATION_BULK_DELETE_TESTS
    + COLLATION_BULK_COLLECTION_DEFAULT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_BULK_WRITE_TESTS))
def test_collation_bulk_write(database_client, collection, test):
    """Test collation behavior in bulkWrite operations."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
