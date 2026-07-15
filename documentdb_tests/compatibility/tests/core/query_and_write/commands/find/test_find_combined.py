"""Tests for find command with multiple options combined."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Combined Operations]: find correctly applies filter, sort, projection,
# skip, limit, and let/$expr together in a single command.
FIND_COMBINED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "filter_sort_projection_skip_limit",
        docs=[{"_id": i, "a": i % 3, "b": i * 10, "c": f"val_{i}"} for i in range(10)],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a": 0},
            "sort": {"b": -1},
            "projection": {"b": 1},
            "skip": 1,
            "limit": 2,
        },
        expected=[{"_id": 6, "b": 60}, {"_id": 3, "b": 30}],
        msg="find should combine filter, sort, projection, skip, and limit correctly.",
    ),
    CommandTestCase(
        "let_expr_sort_projection",
        docs=[
            {"_id": 1, "score": 80, "name": "Alice"},
            {"_id": 2, "score": 95, "name": "Bob"},
            {"_id": 3, "score": 70, "name": "Charlie"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$gte": ["$score", "$$threshold"]}},
            "let": {"threshold": 80},
            "sort": {"score": -1},
            "projection": {"name": 1, "score": 1},
        },
        expected=[
            {"_id": 2, "name": "Bob", "score": 95},
            {"_id": 1, "name": "Alice", "score": 80},
        ],
        msg="find should combine let, $expr, sort, and projection.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_COMBINED_TESTS))
def test_find_combined(database_client, collection, test):
    """Test find command combined operations."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
