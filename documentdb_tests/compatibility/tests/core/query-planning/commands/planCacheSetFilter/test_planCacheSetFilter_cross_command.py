"""Tests for planCacheSetFilter cross-command effectiveness.

Verifies that an index filter set via planCacheSetFilter applies to all
command types that share the same query shape, not just ``find``.  The
parameterized test sets the filter, then verifies via explain that the
winning index switches between case A and case B for each command type.

NOTE: ``find`` is covered by test_planCacheSetFilter_effectiveness.py
(filter-forces-index cases), so it is not repeated here.
"""

from __future__ import annotations

from typing import Any, Callable

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


def _set_filter(collection: Any, query: dict, indexes: list) -> None:
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


def _setup_collection(collection: Any) -> None:
    """Insert docs and create two competing indexes."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(10)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.create_index([("a", 1), ("c", 1)])


# ---------------------------------------------------------------------------
# Command builders — each returns the command dict for explain, given the
# collection name.  The query shape {a: 1} is shared across all of them.
# ---------------------------------------------------------------------------


def _cmd_count(coll_name: str) -> dict:
    return {"count": coll_name, "query": {"a": 1}}


def _cmd_aggregate(coll_name: str) -> dict:
    return {
        "aggregate": coll_name,
        "pipeline": [{"$match": {"a": 1}}],
        "cursor": {},
    }


def _cmd_update(coll_name: str) -> dict:
    return {
        "update": coll_name,
        "updates": [{"q": {"a": 1}, "u": {"$set": {"x": 1}}}],
    }


def _cmd_delete(coll_name: str) -> dict:
    return {
        "delete": coll_name,
        "deletes": [{"q": {"a": 1}, "limit": 0}],
    }


def _cmd_findandmodify(coll_name: str) -> dict:
    return {
        "findAndModify": coll_name,
        "query": {"a": 1},
        "update": {"$set": {"x": 1}},
    }


pytestmark = pytest.mark.admin


# Property [Cross-Command Filter]: The index filter applies to every command
# type that shares the query shape, not just find.
@pytest.mark.parametrize(
    "command_builder",
    [
        pytest.param(_cmd_count, id="count"),
        pytest.param(_cmd_aggregate, id="aggregate"),
        pytest.param(_cmd_update, id="update"),
        pytest.param(_cmd_delete, id="delete"),
        pytest.param(_cmd_findandmodify, id="findAndModify"),
    ],
)
def test_cross_command_filter(collection: Any, command_builder: Callable[[str], dict]) -> None:
    """Test that the index filter applies to the given command type."""
    _setup_collection(collection)

    # Case A: filter to a_1_b_1
    _set_filter(collection, {"a": 1}, [{"a": 1, "b": 1}])
    result = _explain(collection, command_builder(collection.name))
    _assert_explain_index(result, "a_1_b_1", "case A")

    # Case B: filter to a_1_c_1
    _set_filter(collection, {"a": 1}, [{"a": 1, "c": 1}])
    result = _explain(collection, command_builder(collection.name))
    _assert_explain_index(result, "a_1_c_1", "case B")
