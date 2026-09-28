"""Tests for planCacheSetFilter with partial and sparse indexes.

Verifies that index filters interact correctly with partial-filter-
expression indexes and sparse indexes.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


# Property [Partial Index Qualifying]: when the query implies the
# partialFilterExpression, the partial index is used.
def test_partial_index_qualifying(collection):
    """Test planCacheSetFilter to partial index with qualifying query uses the index."""
    collection.insert_many([{"a": i, "b": i} for i in range(10)])
    collection.create_index(
        "a",
        partialFilterExpression={"a": {"$gte": 5}},
        name="a_partial",
    )
    collection.create_index("b")

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": {"$gte": 0}},
            "indexes": [{"a": 1}],
        },
    )

    # a >= 5 implies partialFilterExpression a >= 5.
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": {"a": {"$gte": 5}}},
            "verbosity": "queryPlanner",
        },
    )

    qp = result["queryPlanner"]
    node = qp["winningPlan"]
    winning_index = None
    while node:
        if node.get("stage") in ("IXSCAN", "COUNT_SCAN", "DISTINCT_SCAN"):
            winning_index = node.get("indexName")
            break
        node = node.get("inputStage")

    assertProperties(
        {"indexFilterSet": qp["indexFilterSet"], "winningIndex": winning_index},
        {"indexFilterSet": Eq(True), "winningIndex": Eq("a_partial")},
        msg="qualifying query should use the partial index",
        raw_res=True,
    )


# Property [Partial Index Non-Qualifying]: when the query does not imply
# the partialFilterExpression, the planner falls back to COLLSCAN.
def test_partial_index_non_qualifying(collection):
    """Test planCacheSetFilter to partial index with non-qualifying query falls back to COLLSCAN."""
    collection.insert_many([{"a": i, "b": i} for i in range(10)])
    collection.create_index(
        "a",
        partialFilterExpression={"a": {"$gte": 5}},
        name="a_partial",
    )
    collection.create_index("b")

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": {"$gte": 0}},
            "indexes": [{"a": 1}],
        },
    )

    # a >= 0 does NOT imply partialFilterExpression a >= 5.
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": {"a": {"$gte": 0}}},
            "verbosity": "queryPlanner",
        },
    )

    qp = result["queryPlanner"]
    assertProperties(
        {
            "indexFilterSet": qp["indexFilterSet"],
            "topStage": qp["winningPlan"].get("stage", ""),
        },
        {"indexFilterSet": Eq(True), "topStage": Eq("COLLSCAN")},
        msg="non-qualifying query should fall back to COLLSCAN",
        raw_res=True,
    )


# Property [Sparse Index Qualifying]: when the query qualifies
# ($exists: true), the sparse index is used.
def test_sparse_index_qualifying(collection):
    """Test planCacheSetFilter to sparse index with $exists:true uses the index."""
    collection.insert_many(
        [{"_id": i, "a": i} for i in range(5)] + [{"_id": i + 5, "b": 1} for i in range(5)]
    )
    collection.create_index("a", sparse=True, name="a_sparse")

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": {"$exists": True}},
            "indexes": [{"a": 1}],
        },
    )

    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"a": {"$exists": True}},
            },
            "verbosity": "queryPlanner",
        },
    )

    qp = result["queryPlanner"]
    node = qp["winningPlan"]
    winning_index = None
    while node:
        if node.get("stage") in ("IXSCAN", "COUNT_SCAN", "DISTINCT_SCAN"):
            winning_index = node.get("indexName")
            break
        node = node.get("inputStage")

    assertProperties(
        {"indexFilterSet": qp["indexFilterSet"], "winningIndex": winning_index},
        {"indexFilterSet": Eq(True), "winningIndex": Eq("a_sparse")},
        msg="$exists:true should use the sparse index",
        raw_res=True,
    )


# Property [Sparse Index Non-Qualifying]: when the query does not
# qualify ($exists: false), the planner falls back to COLLSCAN.
def test_sparse_index_non_qualifying(collection):
    """Test planCacheSetFilter to sparse index with $exists:false falls back to COLLSCAN."""
    collection.insert_many(
        [{"_id": i, "a": i} for i in range(5)] + [{"_id": i + 5, "b": 1} for i in range(5)]
    )
    collection.create_index("a", sparse=True, name="a_sparse")

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": {"$exists": False}},
            "indexes": [{"a": 1}],
        },
    )

    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"a": {"$exists": False}},
            },
            "verbosity": "queryPlanner",
        },
    )

    qp = result["queryPlanner"]
    assertProperties(
        {
            "indexFilterSet": qp["indexFilterSet"],
            "topStage": qp["winningPlan"].get("stage", ""),
        },
        {"indexFilterSet": Eq(True), "topStage": Eq("COLLSCAN")},
        msg="$exists:false should fall back to COLLSCAN",
        raw_res=True,
    )
