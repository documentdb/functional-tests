"""$$NOW read path: find with $expr, time-window filtering, view definitions, explain,
and delete."""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import (
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command


@pytest.mark.find
def test_now_in_find_expr_selects_past_documents(collection):
    """Test find with $expr selects only documents whose stored date precedes $$NOW."""
    collection.insert_many(
        [{"_id": 1, "d": datetime(2000, 1, 1)}, {"_id": 2, "d": datetime(2100, 1, 1)}]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$lt": ["$d", "$$NOW"]}},
            "projection": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1}],
        msg="find with $expr should select documents dated before $$NOW",
    )


@pytest.mark.find
def test_now_in_find_expr_selects_future_documents(collection):
    """Test find with $expr selects only documents whose stored date follows $$NOW."""
    collection.insert_many(
        [{"_id": 1, "d": datetime(2000, 1, 1)}, {"_id": 2, "d": datetime(2100, 1, 1)}]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$gt": ["$d", "$$NOW"]}},
            "projection": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 2}],
        msg="find with $expr should select documents dated after $$NOW",
    )


@pytest.mark.find
def test_now_time_window_filtering(collection):
    """Test $$NOW can bound a time window that excludes documents outside it."""
    collection.insert_many(
        [{"_id": 1, "d": datetime(2000, 1, 1)}, {"_id": 2}, {"_id": 3, "d": datetime(2100, 1, 1)}]
    )
    # Seed the in-window date from the server's own clock. Using a client-side datetime here
    # would make the test depend on the client and server clocks agreeing.
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 2}, "u": [{"$addFields": {"d": "$$NOW"}}]}],
        },
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "$expr": {
                    "$and": [
                        {"$gte": ["$d", {"$subtract": ["$$NOW", 3600000]}]},
                        {"$lte": ["$d", "$$NOW"]},
                    ]
                }
            },
            "projection": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 2}],
        msg="A $$NOW-relative time window should select only documents inside it",
    )


@pytest.mark.aggregate
def test_now_in_view_definition_is_constant(collection, request):
    """Test a view computing $$NOW returns one distinct value for all documents."""
    view_name = f"now_view_{request.node.name}"
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    collection.database.command(
        {
            "create": view_name,
            "viewOn": collection.name,
            "pipeline": [{"$addFields": {"t": "$$NOW"}}],
        }
    )
    result = execute_command(
        collection,
        {
            "aggregate": view_name,
            "pipeline": [{"$group": {"_id": "$t"}}, {"$count": "groups"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"groups": 1}],
        msg="A view computing $$NOW should yield a single constant value",
    )


@pytest.mark.find
def test_now_in_find_on_view_with_expr(collection, request):
    """Test find on a $$NOW view with an $expr equality against $$NOW executes."""
    view_name = f"now_view_{request.node.name}"
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    collection.database.command(
        {
            "create": view_name,
            "viewOn": collection.name,
            "pipeline": [{"$addFields": {"t": "$$NOW"}}],
        }
    )
    result = execute_command(
        collection,
        {
            "find": view_name,
            "filter": {"$expr": {"$eq": ["$t", "$$NOW"]}},
            "projection": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="find on a $$NOW view comparing against $$NOW should execute",
        ignore_doc_order=True,
    )


@pytest.mark.find
def test_now_in_find_explain(collection):
    """Test explain of a find whose filter references $$NOW succeeds."""
    collection.insert_many([{"_id": 1, "d": datetime(2000, 1, 1)}])
    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"$expr": {"$lt": ["$d", "$$NOW"]}},
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of a find referencing $$NOW should succeed",
    )


@pytest.mark.aggregate
def test_now_in_aggregate_explain(collection):
    """Test explain of an aggregation that references $$NOW succeeds."""
    collection.insert_many([{"_id": 1}])
    result = execute_command(
        collection,
        {
            "explain": {
                "aggregate": collection.name,
                "pipeline": [{"$addFields": {"t": "$$NOW"}}],
                "cursor": {},
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of an aggregation referencing $$NOW should succeed",
    )


@pytest.mark.delete
def test_now_in_delete_expr(collection):
    """Test $$NOW in a delete filter removes only documents dated before now."""
    collection.insert_many(
        [{"_id": 1, "d": datetime(2000, 1, 1)}, {"_id": 2, "d": datetime(2100, 1, 1)}]
    )
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"$expr": {"$lt": ["$d", "$$NOW"]}}, "limit": 0}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1},
        msg="$$NOW in a delete filter should remove only documents dated before now",
    )
