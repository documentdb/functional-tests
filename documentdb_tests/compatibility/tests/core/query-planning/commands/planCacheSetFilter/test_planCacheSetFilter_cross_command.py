"""Tests for planCacheSetFilter cross-command effectiveness.

Verifies that an index filter set via planCacheSetFilter applies to all
command types that share the same query shape, not just ``find``.  Each
test sets the filter once, then verifies the explain output for the given
command honors the filter by switching indexes between case A and case B.
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


def _explain(collection: Any, cmd: dict) -> Any:
    """Run explain for a command and return the full explain result."""
    return execute_command(
        collection,
        {"explain": cmd, "verbosity": "queryPlanner"},
    )


def _assert_explain_index(result: dict, expected_index: str, msg: str) -> None:
    """Assert indexFilterSet is True and winning index matches."""
    assertProperties(
        result,
        {"queryPlanner.indexFilterSet": Eq(True)},
        msg=msg,
        raw_res=True,
    )
    wp = result["queryPlanner"]["winningPlan"]
    idx = _get_winning_index(wp)
    assertProperties(
        {"idx": idx},
        {"idx": Eq(expected_index)},
        msg=f"{msg} — winning index",
        raw_res=True,
    )


def _setup_collection(collection):
    """Insert docs and create two competing indexes."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(10)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.create_index([("a", 1), ("c", 1)])


pytestmark = pytest.mark.admin


# ---------------------------------------------------------------------------
# Property [Cross-Command Filter: find]: find honors the index filter.
# ---------------------------------------------------------------------------


def test_cross_command_find(collection):
    """Test find honors index filter — case A then case B."""
    _setup_collection(collection)

    _set_filter(collection, {"a": 1}, [{"a": 1, "b": 1}])
    result = _explain(collection, {"find": collection.name, "filter": {"a": 1}})
    _assert_explain_index(result, "a_1_b_1", "find case A")

    _set_filter(collection, {"a": 1}, [{"a": 1, "c": 1}])
    result = _explain(collection, {"find": collection.name, "filter": {"a": 1}})
    _assert_explain_index(result, "a_1_c_1", "find case B")


# ---------------------------------------------------------------------------
# Property [Cross-Command Filter: count]: count honors the index filter.
# ---------------------------------------------------------------------------


def test_cross_command_count(collection):
    """Test count honors index filter — case A then case B."""
    _setup_collection(collection)

    _set_filter(collection, {"a": 1}, [{"a": 1, "b": 1}])
    result = _explain(collection, {"count": collection.name, "query": {"a": 1}})
    _assert_explain_index(result, "a_1_b_1", "count case A")

    _set_filter(collection, {"a": 1}, [{"a": 1, "c": 1}])
    result = _explain(collection, {"count": collection.name, "query": {"a": 1}})
    _assert_explain_index(result, "a_1_c_1", "count case B")


# ---------------------------------------------------------------------------
# Property [Cross-Command Filter: aggregate $match]: aggregate with a
# leading $match stage honors the index filter.
# ---------------------------------------------------------------------------


def test_cross_command_aggregate(collection):
    """Test aggregate with $match honors index filter — case A then case B."""
    _setup_collection(collection)

    _set_filter(collection, {"a": 1}, [{"a": 1, "b": 1}])
    result = _explain(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"a": 1}}],
            "cursor": {},
        },
    )
    _assert_explain_index(result, "a_1_b_1", "aggregate case A")

    _set_filter(collection, {"a": 1}, [{"a": 1, "c": 1}])
    result = _explain(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"a": 1}}],
            "cursor": {},
        },
    )
    _assert_explain_index(result, "a_1_c_1", "aggregate case B")


# ---------------------------------------------------------------------------
# Property [Cross-Command Filter: update]: update honors the index filter.
# ---------------------------------------------------------------------------


def test_cross_command_update(collection):
    """Test update honors index filter — case A then case B."""
    _setup_collection(collection)

    _set_filter(collection, {"a": 1}, [{"a": 1, "b": 1}])
    result = _explain(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"a": 1}, "u": {"$set": {"x": 1}}}],
        },
    )
    _assert_explain_index(result, "a_1_b_1", "update case A")

    _set_filter(collection, {"a": 1}, [{"a": 1, "c": 1}])
    result = _explain(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"a": 1}, "u": {"$set": {"x": 1}}}],
        },
    )
    _assert_explain_index(result, "a_1_c_1", "update case B")


# ---------------------------------------------------------------------------
# Property [Cross-Command Filter: delete]: delete honors the index filter.
# ---------------------------------------------------------------------------


def test_cross_command_delete(collection):
    """Test delete honors index filter — case A then case B."""
    _setup_collection(collection)

    _set_filter(collection, {"a": 1}, [{"a": 1, "b": 1}])
    result = _explain(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"a": 1}, "limit": 0}],
        },
    )
    _assert_explain_index(result, "a_1_b_1", "delete case A")

    _set_filter(collection, {"a": 1}, [{"a": 1, "c": 1}])
    result = _explain(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"a": 1}, "limit": 0}],
        },
    )
    _assert_explain_index(result, "a_1_c_1", "delete case B")


# ---------------------------------------------------------------------------
# Property [Cross-Command Filter: findAndModify]: findAndModify honors
# the index filter.
# ---------------------------------------------------------------------------


def test_cross_command_findandmodify(collection):
    """Test findAndModify honors index filter — case A then case B."""
    _setup_collection(collection)

    _set_filter(collection, {"a": 1}, [{"a": 1, "b": 1}])
    result = _explain(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"a": 1},
            "update": {"$set": {"x": 1}},
        },
    )
    _assert_explain_index(result, "a_1_b_1", "findAndModify case A")

    _set_filter(collection, {"a": 1}, [{"a": 1, "c": 1}])
    result = _explain(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"a": 1},
            "update": {"$set": {"x": 1}},
        },
    )
    _assert_explain_index(result, "a_1_c_1", "findAndModify case B")
