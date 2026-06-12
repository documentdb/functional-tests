"""Delete command core behavior tests.

Tests limit behavior, query variations, non-existent collections, response structure,
and document removal verification.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Limit Zero]: limit:0 removes all matching documents.
LIMIT_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "limit_zero_removes_all",
        docs=[{"_id": i, "status": "D"} for i in range(5)] + [{"_id": 99, "status": "A"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"status": "D"}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 5},
        msg="delete should remove all matching documents when limit is 0",
    ),
    CommandTestCase(
        "limit_one_removes_single",
        docs=[{"_id": i, "status": "D"} for i in range(5)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"status": "D"}, "limit": 1}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should remove exactly one document when limit is 1",
    ),
    CommandTestCase(
        "empty_query_limit_zero_removes_all",
        docs=[{"_id": i} for i in range(3)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 3},
        msg="delete should remove all documents with empty query and limit 0",
    ),
    CommandTestCase(
        "empty_query_limit_one",
        docs=[{"_id": i} for i in range(3)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 1}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should remove one document with empty query and limit 1",
    ),
    CommandTestCase(
        "no_match_returns_zero",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": 999}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 0},
        msg="delete should return n:0 when no documents match",
    ),
    CommandTestCase(
        "nonexistent_collection",
        docs=None,
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 0},
        msg="delete should succeed with n:0 on non-existent collection",
    ),
]

# Property [Query Operators]: delete correctly matches using standard query operators.
QUERY_VARIATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comparison_gt",
        docs=[{"_id": i, "val": i} for i in range(5)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"val": {"$gt": 2}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should match documents with $gt query",
    ),
    CommandTestCase(
        "in_operator",
        docs=[{"_id": i, "status": chr(65 + i)} for i in range(5)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"status": {"$in": ["A", "C"]}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should match documents with $in query",
    ),
    CommandTestCase(
        "logical_and",
        docs=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$and": [{"a": 1}, {"b": 10}]}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match documents with $and query",
    ),
    CommandTestCase(
        "regex_query",
        docs=[
            {"_id": 1, "name": "alpha"},
            {"_id": 2, "name": "beta"},
            {"_id": 3, "name": "gamma"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"name": {"$regex": "^a"}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match documents with regex query",
    ),
    CommandTestCase(
        "dot_notation_nested",
        docs=[{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a.b": 1}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match using dot notation",
    ),
    CommandTestCase(
        "exists_true",
        docs=[{"_id": 1, "a": 1}, {"_id": 2}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": {"$exists": True}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match with $exists:true",
    ),
    CommandTestCase(
        "elemmatch_array",
        docs=[
            {"_id": 1, "items": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]},
            {"_id": 2, "items": [{"x": 5, "y": 6}]},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"items": {"$elemMatch": {"x": 1, "y": 2}}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match with $elemMatch",
    ),
]

DELETE_CORE_TESTS: list[CommandTestCase] = LIMIT_BEHAVIOR_TESTS + QUERY_VARIATION_TESTS


@pytest.mark.parametrize("test", pytest_params(DELETE_CORE_TESTS))
def test_delete_core_behavior(database_client, collection, test):
    """Test delete command core behavior."""
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


def test_delete_verifies_document_removal(collection):
    """Test delete removes documents from the collection."""
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    execute_command(
        collection,
        {"delete": collection.name, "deletes": [{"q": {"_id": 1}, "limit": 1}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(result, [{"_id": 2, "a": 2}], msg="delete should have removed the document")
