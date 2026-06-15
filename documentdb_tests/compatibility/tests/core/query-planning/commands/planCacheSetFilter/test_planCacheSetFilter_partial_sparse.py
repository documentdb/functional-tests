"""Tests for planCacheSetFilter with partial and sparse indexes.

Verifies that index filters interact correctly with partial-filter-
expression indexes and sparse indexes.
"""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq


def _get_winning_index(plan: dict) -> str | None:
    """Walk the explain winning plan tree and return the first index name."""
    stage = plan.get("stage")
    if stage in ("IXSCAN", "COUNT_SCAN", "DISTINCT_SCAN"):
        return plan.get("indexName")
    for key in ("inputStage", "inputStages"):
        child = plan.get(key)
        if isinstance(child, dict):
            result = _get_winning_index(child)
            if result:
                return result
        elif isinstance(child, list):
            for entry in child:
                result = _get_winning_index(entry)
                if result:
                    return result
    return None


def _explain_find(collection: Any, query: dict) -> Any:
    """Run explain for a find command and return the full explain result."""
    return execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": query},
            "verbosity": "queryPlanner",
        },
    )


def _set_filter(collection, query: dict, indexes: list) -> None:
    """Set an index filter via planCacheSetFilter."""
    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": query,
            "indexes": indexes,
        },
    )


def _assert_explain(
    result: dict,
    *,
    index_filter_set: bool,
    expected_index: str | None = None,
    expected_stage: str | None = None,
    msg: str,
) -> None:
    """Assert explain result properties using framework assertions."""
    assertProperties(
        result,
        {"queryPlanner.indexFilterSet": Eq(index_filter_set)},
        msg=msg,
        raw_res=True,
    )
    wp = result["queryPlanner"]["winningPlan"]
    if expected_index is not None:
        idx = _get_winning_index(wp)
        assertProperties(
            {"idx": idx},
            {"idx": Eq(expected_index)},
            msg=f"{msg} — winning index",
            raw_res=True,
        )
    if expected_stage is not None:
        assertProperties(
            wp,
            {"stage": Eq(expected_stage)},
            msg=f"{msg} — winning stage",
            raw_res=True,
        )


pytestmark = pytest.mark.admin


# ---------------------------------------------------------------------------
# Property [Partial Index — Qualifying Query]: When the filter targets a
# partial index and the query predicate implies the partialFilterExpression,
# the winning plan uses the partial index.
# ---------------------------------------------------------------------------


def test_partial_index_qualifying(collection):
    """Test filter to partial index with qualifying query uses the index."""
    collection.insert_many([{"a": i, "b": i} for i in range(10)])
    collection.create_index(
        "a",
        partialFilterExpression={"a": {"$gte": 5}},
        name="a_partial",
    )
    collection.create_index("b")

    _set_filter(collection, {"a": {"$gte": 0}}, [{"a": 1}])

    # a >= 5 implies partialFilterExpression a >= 5
    result = _explain_find(collection, {"a": {"$gte": 5}})
    _assert_explain(
        result,
        index_filter_set=True,
        expected_index="a_partial",
        msg="qualifying query should use the partial index",
    )


# ---------------------------------------------------------------------------
# Property [Partial Index — Non-Qualifying Query]: When the filter targets
# a partial index but the query does NOT imply the partialFilterExpression,
# the planner cannot use the partial index and falls back to COLLSCAN.
# ---------------------------------------------------------------------------


def test_partial_index_non_qualifying(collection):
    """Test filter to partial index with non-qualifying query falls back to COLLSCAN."""
    collection.insert_many([{"a": i, "b": i} for i in range(10)])
    collection.create_index(
        "a",
        partialFilterExpression={"a": {"$gte": 5}},
        name="a_partial",
    )
    collection.create_index("b")

    _set_filter(collection, {"a": {"$gte": 0}}, [{"a": 1}])

    # a >= 0 does NOT imply partialFilterExpression a >= 5
    result = _explain_find(collection, {"a": {"$gte": 0}})
    _assert_explain(
        result,
        index_filter_set=True,
        expected_stage="COLLSCAN",
        msg="non-qualifying query should fall back to COLLSCAN",
    )


# ---------------------------------------------------------------------------
# Property [Sparse Index — Qualifying Query]: When the filter targets a
# sparse index and the query qualifies ({$exists: true}), the winning
# plan uses the sparse index.
# ---------------------------------------------------------------------------


def test_sparse_index_qualifying(collection):
    """Test filter to sparse index with $exists:true uses the index."""
    collection.insert_many(
        [{"_id": i, "a": i} for i in range(5)] + [{"_id": i + 5, "b": 1} for i in range(5)]
    )
    collection.create_index("a", sparse=True, name="a_sparse")

    _set_filter(collection, {"a": {"$exists": True}}, [{"a": 1}])

    result = _explain_find(collection, {"a": {"$exists": True}})
    _assert_explain(
        result,
        index_filter_set=True,
        expected_index="a_sparse",
        msg="$exists:true should use the sparse index",
    )


# ---------------------------------------------------------------------------
# Property [Sparse Index — Non-Qualifying Query]: When the filter targets
# a sparse index and the query does NOT qualify ({$exists: false}), the
# planner falls back to COLLSCAN.  Note: {$exists: false} produces a
# different query shape than {$exists: true}, so each shape needs its own
# filter.
# ---------------------------------------------------------------------------


def test_sparse_index_non_qualifying(collection):
    """Test filter to sparse index with $exists:false falls back to COLLSCAN."""
    collection.insert_many(
        [{"_id": i, "a": i} for i in range(5)] + [{"_id": i + 5, "b": 1} for i in range(5)]
    )
    collection.create_index("a", sparse=True, name="a_sparse")

    _set_filter(collection, {"a": {"$exists": False}}, [{"a": 1}])

    result = _explain_find(collection, {"a": {"$exists": False}})
    _assert_explain(
        result,
        index_filter_set=True,
        expected_stage="COLLSCAN",
        msg="$exists:false should fall back to COLLSCAN",
    )
