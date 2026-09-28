"""Tests for explain command core behavior.

Covers the explainable command surface (find, aggregate, count, distinct,
update, delete, findAndModify), edge cases (empty / non-existent collection,
complex and $expr filters, $lookup sub-pipeline), and plan-cache interaction
(explain does not create plan cache entries).
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists

pytestmark = pytest.mark.admin


SUPPORTED_COMMAND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="find",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {"explain": {"find": ctx.collection, "filter": {"a": 1}}},
        expected={"ok": Eq(1.0)},
        msg="explain should plan the find command",
    ),
    CommandTestCase(
        id="aggregate_single",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"a": 1}}],
                "cursor": {},
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan the aggregate_single command",
    ),
    CommandTestCase(
        id="aggregate_multi",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {
                "aggregate": ctx.collection,
                "pipeline": [
                    {"$match": {"a": {"$gt": 0}}},
                    {"$group": {"_id": None, "c": {"$sum": 1}}},
                ],
                "cursor": {},
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan the aggregate_multi command",
    ),
    CommandTestCase(
        id="count",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {"explain": {"count": ctx.collection, "query": {"a": 1}}},
        expected={"ok": Eq(1.0)},
        msg="explain should plan the count command",
    ),
    CommandTestCase(
        id="distinct",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {"explain": {"distinct": ctx.collection, "key": "a"}},
        expected={"ok": Eq(1.0)},
        msg="explain should plan the distinct command",
    ),
    CommandTestCase(
        id="update_single",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {
                "update": ctx.collection,
                "updates": [{"q": {"a": 1}, "u": {"$set": {"b": 9}}}],
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan the update_single command",
    ),
    CommandTestCase(
        id="update_multi",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {
                "update": ctx.collection,
                "updates": [{"q": {"a": {"$gt": 0}}, "u": {"$set": {"b": 9}}, "multi": True}],
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan the update_multi command",
    ),
    CommandTestCase(
        id="delete_single",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {"delete": ctx.collection, "deletes": [{"q": {"a": 1}, "limit": 1}]}
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan the delete_single command",
    ),
    CommandTestCase(
        id="delete_multi",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {
                "delete": ctx.collection,
                "deletes": [{"q": {"a": {"$gt": 0}}, "limit": 0}],
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan the delete_multi command",
    ),
    CommandTestCase(
        id="findAndModify",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {
                "findAndModify": ctx.collection,
                "query": {"a": 1},
                "update": {"$set": {"b": 9}},
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan the findAndModify command",
    ),
    CommandTestCase(
        id="find_returns_query_planner",
        docs=[{"_id": i, "a": i, "b": i} for i in range(5)],
        command=lambda ctx: {"explain": {"find": ctx.collection, "filter": {"a": 1}}},
        expected={"queryPlanner": Exists()},
        msg="find explain has queryPlanner",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUPPORTED_COMMAND_TESTS))
def test_explain_supported_commands(collection, test):
    """Test explain plans each supported command and exposes planner output."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="empty_collection",
        docs=[],
        command=lambda ctx: {"explain": {"find": ctx.collection, "filter": {"a": 1}}},
        expected={"ok": Eq(1.0)},
        msg="explain on empty collection should succeed",
    ),
    CommandTestCase(
        id="non_existent_collection",
        command=lambda ctx: {
            "explain": {"find": f"{ctx.collection}_nonexistent", "filter": {"a": 1}}
        },
        expected={"ok": Eq(1.0)},
        msg="explain on non-existent collection should succeed",
    ),
    CommandTestCase(
        id="complex_nested_query",
        docs=[{"_id": i, "a": i, "b": i % 2} for i in range(10)],
        command=lambda ctx: {
            "explain": {
                "find": ctx.collection,
                "filter": {
                    "$and": [
                        {"$or": [{"a": {"$lt": 3}}, {"a": {"$gt": 7}}]},
                        {"$or": [{"b": 0}, {"b": 1}]},
                    ]
                },
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan a complex nested query",
    ),
    CommandTestCase(
        id="expr_in_filter",
        docs=[{"_id": i, "a": i, "b": i + 1} for i in range(5)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"$expr": {"$gt": ["$b", "$a"]}}}
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan an $expr filter",
    ),
    CommandTestCase(
        id="aggregate_lookup_subpipeline",
        docs=[{"_id": i, "a": i} for i in range(5)],
        command=lambda ctx: {
            "explain": {
                "aggregate": ctx.collection,
                "pipeline": [
                    {
                        "$lookup": {
                            "from": ctx.collection,
                            "let": {"av": "$a"},
                            "pipeline": [{"$match": {"$expr": {"$eq": ["$a", "$$av"]}}}],
                            "as": "matches",
                        }
                    }
                ],
                "cursor": {},
            }
        },
        expected={"ok": Eq(1.0)},
        msg="explain should plan a $lookup sub-pipeline",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_explain_edge_cases(collection, test):
    """Test explain succeeds across collection-state and filter edge cases."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_explain_does_not_create_plan_cache_entry(collection):
    """Test explain does not create a plan cache entry for the planned query."""
    collection.insert_many([{"_id": i, "a": i % 5, "b": i % 3} for i in range(50)])
    collection.create_index([("a", 1)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.database.command({"planCacheClear": collection.name})
    execute_command(collection, {"explain": {"find": collection.name, "filter": {"a": 2, "b": 1}}})

    cache = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$planCacheStats": {}}], "cursor": {}},
    )
    assertSuccess(cache, [], msg="explain should not create plan cache entries")
