"""Tests for collation interaction with command-level let variables."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Aggregate Let Variables with Collation]: command-level let variables
# used in $expr comparisons respect the command collation.
COLLATION_AGGREGATE_LET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "aggregate_let_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$x", "$$target"]}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "let": {"target": "apple"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="aggregate let variable comparison should use command collation",
    ),
    CommandTestCase(
        "aggregate_let_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$x", "$$target"]}}},
            ],
            "cursor": {},
            "let": {"target": "apple"},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="aggregate let variable comparison without collation should use binary matching",
    ),
]

# Property [Find Let Variables with Collation]: command-level let variables
# used in $expr comparisons in find respect the command collation.
COLLATION_FIND_LET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_let_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$x", "$$target"]}},
            "sort": {"_id": 1},
            "let": {"target": "apple"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="find let variable comparison should use command collation",
    ),
    CommandTestCase(
        "find_let_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$x", "$$target"]}},
            "let": {"target": "apple"},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find let variable comparison without collation should use binary matching",
    ),
]

# Property [Update Let Variables with Collation]: command-level let variables
# used in $expr filter comparisons in update respect the per-statement collation.
COLLATION_UPDATE_LET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_let_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple", "v": 0},
            {"_id": 2, "x": "Apple", "v": 0},
            {"_id": 3, "x": "banana", "v": 0},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"$expr": {"$eq": ["$x", "$$target"]}},
                    "u": {"$set": {"v": 1}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
            "let": {"target": "apple"},
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="update let variable comparison should use per-statement collation",
    ),
    CommandTestCase(
        "update_let_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple", "v": 0},
            {"_id": 2, "x": "Apple", "v": 0},
            {"_id": 3, "x": "banana", "v": 0},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"$expr": {"$eq": ["$x", "$$target"]}},
                    "u": {"$set": {"v": 1}},
                    "multi": True,
                }
            ],
            "let": {"target": "apple"},
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="update let variable comparison without collation should use binary matching",
    ),
]

COLLATION_LET_TESTS: list[CommandTestCase] = (
    COLLATION_AGGREGATE_LET_TESTS + COLLATION_FIND_LET_TESTS + COLLATION_UPDATE_LET_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_LET_TESTS))
def test_collation_let_variables(database_client, collection, test):
    """Test collation interaction with command-level let variables."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(test.build_expected(ctx), list),
    )
