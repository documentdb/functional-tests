"""Tests for find command $expr in filter and let variables."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [$expr and let]: find resolves $expr expressions and let variables
# in filter context, and let variables require $expr to be resolved.
FIND_LET_EXPR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_comparison",
        docs=[{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 1, "b": 10}, {"_id": 3, "a": 7, "b": 7}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$gt": ["$a", "$b"]}},
            "sort": {"_id": 1},
        },
        expected=[{"_id": 1, "a": 5, "b": 3}],
        msg="find should match docs where $a > $b via $expr.",
    ),
    CommandTestCase(
        "expr_equality",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"$expr": {"$eq": ["$a", 5]}}},
        expected=[{"_id": 1, "a": 5}],
        msg="find should match docs where $a equals literal via $expr.",
    ),
    CommandTestCase(
        "expr_arithmetic",
        docs=[{"_id": 1, "a": 8}, {"_id": 2, "a": 15}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$gt": [{"$add": ["$a", 1]}, 10]}},
        },
        expected=[{"_id": 2, "a": 15}],
        msg="find should match via $expr with arithmetic.",
    ),
    CommandTestCase(
        "let_variable_with_expr",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": 10}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$a", "$$target"]}},
            "let": {"target": 5},
        },
        expected=[{"_id": 1, "a": 5}],
        msg="find should resolve let variable in $expr filter.",
    ),
    CommandTestCase(
        "let_multiple_variables",
        docs=[{"_id": 1, "a": 5, "b": 10}, {"_id": 2, "a": 3, "b": 7}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$and": [{"$gte": ["$a", "$$lo"]}, {"$lte": ["$b", "$$hi"]}]}},
            "let": {"lo": 4, "hi": 10},
        },
        expected=[{"_id": 1, "a": 5, "b": 10}],
        msg="find should resolve multiple let variables in $expr.",
    ),
    CommandTestCase(
        "let_variable_string",
        docs=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$name", "$$who"]}},
            "let": {"who": "Alice"},
        },
        expected=[{"_id": 1, "name": "Alice"}],
        msg="find should resolve string let variable in $expr.",
    ),
    CommandTestCase(
        "let_variable_null",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$a", "$$val"]}},
            "let": {"val": None},
        },
        expected=[{"_id": 1, "a": None}],
        msg="find should resolve null let variable in $expr.",
    ),
    CommandTestCase(
        "let_not_resolved_without_expr",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": "$$target"}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a": "$$target"},
            "let": {"target": 5},
        },
        expected=[{"_id": 2, "a": "$$target"}],
        msg="find should not resolve let variable without $expr.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_LET_EXPR_TESTS))
def test_find_let_expr(database_client, collection, test):
    """Test find command $expr and let variable behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
