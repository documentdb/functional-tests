"""Delete command options tests.

Tests hint, collation wiring, let variables, comment, ordered, and writeConcern.
"""

from __future__ import annotations

import pytest
from pymongo import ASCENDING, IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Option Acceptance]: the delete command accepts all documented optional fields.
DELETE_OPTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_index_spec_document",
        docs=[{"_id": i, "status": "D"} for i in range(3)],
        indexes=[IndexModel([("status", ASCENDING)])],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"status": "D"}, "limit": 0, "hint": {"status": 1}}],
        },
        expected={"ok": 1.0, "n": 3},
        msg="delete should accept hint as index spec document",
    ),
    CommandTestCase(
        "hint_index_name_string",
        docs=[{"_id": i, "status": "D"} for i in range(2)],
        indexes=[IndexModel([("status", ASCENDING)], name="status_idx")],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"status": "D"}, "limit": 0, "hint": "status_idx"}],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should accept hint as index name string",
    ),
    CommandTestCase(
        "hint_id_index",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1, "hint": {"_id": 1}}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept _id index hint",
    ),
    CommandTestCase(
        "hint_compound_index",
        docs=[{"_id": i, "a": 1, "b": i} for i in range(3)],
        indexes=[IndexModel([("a", ASCENDING), ("b", ASCENDING)])],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": 1, "b": 1}, "limit": 1, "hint": {"a": 1, "b": 1}}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept compound index hint",
    ),
    CommandTestCase(
        "let_string_variable",
        docs=[{"_id": 1, "status": "active"}, {"_id": 2, "status": "inactive"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$eq": ["$status", "$$target"]}}, "limit": 0}],
            "let": {"target": "inactive"},
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should resolve string let variable",
    ),
    CommandTestCase(
        "let_numeric_variable",
        docs=[{"_id": i, "score": i * 10} for i in range(5)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$lt": ["$score", "$$threshold"]}}, "limit": 0}],
            "let": {"threshold": 30},
        },
        expected={"ok": 1.0, "n": 3},
        msg="delete should resolve numeric let variable",
    ),
    CommandTestCase(
        "let_array_variable",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$in": ["$_id", "$$ids"]}}, "limit": 0}],
            "let": {"ids": [1, 3]},
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should resolve array let variable",
    ),
    CommandTestCase(
        "let_empty_document",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "let": {},
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept empty let document",
    ),
    CommandTestCase(
        "comment_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "comment": "test deletion",
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept string comment",
    ),
    CommandTestCase(
        "comment_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "comment": {"app": "test", "op": "cleanup"},
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept object comment",
    ),
    CommandTestCase(
        "ordered_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "ordered": True,
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept ordered:true",
    ),
    CommandTestCase(
        "ordered_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "ordered": False,
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept ordered:false",
    ),
    CommandTestCase(
        "writeconcern_w1",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept writeConcern w:1",
    ),
    CommandTestCase(
        "writeconcern_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "writeConcern": {"w": "majority"},
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should accept writeConcern w:majority",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DELETE_OPTIONS_TESTS))
def test_delete_options(database_client, collection, test):
    """Test delete command options acceptance."""
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


def test_delete_collation_case_insensitive_wiring(collection):
    """Test delete accepts collation for case-insensitive matching."""
    collection.insert_many(
        [
            {"_id": 1, "name": "Cafe"},
            {"_id": 2, "name": "cafe"},
            {"_id": 3, "name": "CAFE"},
        ]
    )
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [
                {"q": {"name": "cafe"}, "limit": 0, "collation": {"locale": "en", "strength": 2}}
            ],
        },
    )
    assertResult(
        result,
        expected={"ok": 1.0, "n": 3},
        msg="delete should use collation for case-insensitive match",
        raw_res=True,
    )
