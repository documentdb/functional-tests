"""Delete command $expr filter tests.

Tests $expr usage in delete query filters per Rule 17.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [$expr Support]: delete resolves $expr filter expressions including cross-field
# comparisons, logical operators, nested expressions, and let variables.
DELETE_EXPR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_equality",
        docs=[{"_id": 1, "status": "D"}, {"_id": 2, "status": "A"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$eq": ["$status", "D"]}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match via $expr $eq",
    ),
    CommandTestCase(
        "expr_cross_field_comparison",
        docs=[{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 1, "b": 10}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$gt": ["$a", "$b"]}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match via $expr cross-field comparison",
    ),
    CommandTestCase(
        "expr_and_logic",
        docs=[
            {"_id": 1, "a": 5, "b": 3},
            {"_id": 2, "a": 1, "b": 8},
            {"_id": 3, "a": 5, "b": 8},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"$expr": {"$and": [{"$gt": ["$a", 2]}, {"$gt": ["$b", 5]}]}}, "limit": 0}
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should support $and inside $expr",
    ),
    CommandTestCase(
        "expr_nested_expression",
        docs=[
            {"_id": 1, "price": 100, "discount": 0.2},
            {"_id": 2, "price": 50, "discount": 0.1},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {
                        "$expr": {
                            "$lt": [
                                {"$multiply": ["$price", {"$subtract": [1, "$discount"]}]},
                                60,
                            ]
                        }
                    },
                    "limit": 0,
                }
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should support nested expressions in $expr",
    ),
    CommandTestCase(
        "expr_with_let_variable",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": -1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$eq": ["$a", "$$target"]}}, "limit": 0}],
            "let": {"target": -1},
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should resolve $$variable in $expr",
    ),
    CommandTestCase(
        "expr_no_match",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$gt": ["$a", 100]}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 0},
        msg="delete should return n:0 when $expr matches nothing",
    ),
    CommandTestCase(
        "expr_matches_all",
        docs=[{"_id": i, "a": i} for i in range(3)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$gte": ["$a", 0]}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 3},
        msg="delete should delete all when $expr matches all",
    ),
    CommandTestCase(
        "expr_nonexistent_field",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"$expr": {"$gt": ["$nonexistent", 0]}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 0},
        msg="delete should not match when $expr references missing field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DELETE_EXPR_TESTS))
def test_delete_with_expr(database_client, collection, test):
    """Test delete command $expr filter support."""
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
