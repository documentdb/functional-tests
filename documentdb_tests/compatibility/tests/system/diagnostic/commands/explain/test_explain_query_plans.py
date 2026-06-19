"""Tests for explain query-plan and index-usage output.

Covers collection-scan vs index-scan plan selection, the plan change after an
index is created, aggregate query-planner output, and executionStats counts for
hinted queries and $limit pipelines (including after additional inserts).

Assertions favor portable signals (nReturned, plan stage presence) over
engine-specific internal plan-node details.
"""

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Ne

pytestmark = pytest.mark.admin


def test_explain_uses_collscan_without_index(collection):
    """Test explain reports COLLSCAN when no usable index exists."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    result = execute_command(collection, {"explain": {"find": collection.name, "filter": {"a": 5}}})
    assertProperties(
        result,
        {"queryPlanner.winningPlan.stage": Eq("COLLSCAN")},
        raw_res=True,
        msg="plan should be COLLSCAN before index creation",
    )


def test_explain_avoids_collscan_after_index_created(collection):
    """Test explain stops using COLLSCAN after a matching index is created."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    collection.create_index([("a", 1)])
    result = execute_command(collection, {"explain": {"find": collection.name, "filter": {"a": 5}}})
    assertProperties(
        result,
        {"queryPlanner.winningPlan.stage": Ne("COLLSCAN")},
        raw_res=True,
        msg="plan should use an index (not COLLSCAN) after index creation",
    )


def test_explain_aggregate_contains_query_planner(collection):
    """Test explain for an aggregate returns a queryPlanner section."""
    collection.insert_many([{"_id": i, "a": i % 3} for i in range(20)])
    result = execute_command(
        collection,
        {
            "explain": {
                "aggregate": collection.name,
                "pipeline": [{"$match": {"a": 1}}],
                "cursor": {},
            }
        },
    )
    assertProperties(
        result,
        {"queryPlanner": Exists()},
        raw_res=True,
        msg="aggregate explain should contain a queryPlanner section",
    )


EXEC_STATS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="hint_nReturned",
        docs=[{"_id": i, "a": i, "b": i % 2} for i in range(10)],
        indexes=[IndexModel([("a", 1)])],
        command=lambda ctx: {
            "explain": {
                "find": ctx.collection,
                "filter": {"a": {"$gte": 0}},
                "sort": {"a": 1},
                "hint": {"a": 1},
            },
            "verbosity": "executionStats",
        },
        expected={"executionStats.nReturned": Eq(10)},
        msg="explain with hint should report correct nReturned",
    ),
    CommandTestCase(
        id="limit_executionStats_nReturned",
        docs=[{"_id": i, "a": i} for i in range(20)],
        command=lambda ctx: {
            "explain": {"aggregate": ctx.collection, "pipeline": [{"$limit": 5}], "cursor": {}},
            "verbosity": "executionStats",
        },
        expected={"executionStats.nReturned": Eq(5)},
        msg="executionStats nReturned should match the limit",
    ),
    CommandTestCase(
        id="limit_allPlansExecution_nReturned",
        docs=[{"_id": i, "a": i} for i in range(20)],
        command=lambda ctx: {
            "explain": {"aggregate": ctx.collection, "pipeline": [{"$limit": 5}], "cursor": {}},
            "verbosity": "allPlansExecution",
        },
        expected={"executionStats.nReturned": Eq(5)},
        msg="allPlansExecution should honor the limit",
    ),
    CommandTestCase(
        id="limit_multiple_indexes_nReturned",
        docs=[{"_id": i, "a": i % 5, "b": i % 3} for i in range(60)],
        indexes=[IndexModel([("a", 1)]), IndexModel([("a", 1), ("b", 1)])],
        command=lambda ctx: {
            "explain": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"a": 2, "b": 1}}, {"$limit": 3}],
                "cursor": {},
            },
            "verbosity": "executionStats",
        },
        expected={"executionStats.nReturned": Eq(3)},
        msg="limit should be honored with multiple candidate indexes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXEC_STATS_TESTS))
def test_explain_execution_stats(collection, test):
    """Test explain executionStats reports counts matching hints and limits."""
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


def test_explain_results_update_after_inserts(collection):
    """Test explain executionStats reflects newly inserted documents."""
    collection.insert_many([{"_id": i, "a": i} for i in range(10)])
    collection.create_index([("a", 1)])
    query = {
        "explain": {"find": collection.name, "filter": {"a": {"$gte": 0}}, "hint": {"a": 1}},
        "verbosity": "executionStats",
    }
    execute_command(collection, query)
    collection.insert_many([{"_id": i, "a": i} for i in range(10, 15)])
    after = execute_command(collection, query)
    assertProperties(
        after,
        {"executionStats.nReturned": Eq(15)},
        raw_res=True,
        msg="explain should reflect additional inserted documents",
    )
