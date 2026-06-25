"""Tests for planCacheSetFilter cross-command effectiveness.

Verifies that an index filter set via planCacheSetFilter applies to all
command types that share the same query shape, not just find.

NOTE: find is covered by test_planCacheSetFilter_effectiveness.py
(filter-forces-index cases), so it is not repeated here.
"""

from __future__ import annotations

from typing import Any, Callable

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


# Property [Cross-Command Filter]: the index filter applies to every
# command type that shares the query shape.
@pytest.mark.parametrize(
    "filter_indexes,expected_index",
    [
        pytest.param([{"a": 1, "b": 1}], "a_1_b_1", id="case_A"),
        pytest.param([{"a": 1, "c": 1}], "a_1_c_1", id="case_B"),
    ],
)
@pytest.mark.parametrize(
    "command_builder",
    [
        pytest.param(
            lambda n: {"count": n, "query": {"a": 1}},
            id="count",
        ),
        pytest.param(
            lambda n: {
                "aggregate": n,
                "pipeline": [{"$match": {"a": 1}}],
                "cursor": {},
            },
            id="aggregate",
        ),
        pytest.param(
            lambda n: {
                "update": n,
                "updates": [{"q": {"a": 1}, "u": {"$set": {"x": 1}}}],
            },
            id="update",
        ),
        pytest.param(
            lambda n: {
                "delete": n,
                "deletes": [{"q": {"a": 1}, "limit": 0}],
            },
            id="delete",
        ),
        pytest.param(
            lambda n: {
                "findAndModify": n,
                "query": {"a": 1},
                "update": {"$set": {"x": 1}},
            },
            id="findAndModify",
        ),
        pytest.param(
            lambda n: {
                "distinct": n,
                "key": "a",
                "query": {"a": 1},
            },
            id="distinct",
        ),
    ],
)
def test_cross_command_filter(
    collection: Any,
    command_builder: Callable[[str], dict],
    filter_indexes: list,
    expected_index: str,
) -> None:
    """Test planCacheSetFilter applies to the given command type."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(10)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.create_index([("a", 1), ("c", 1)])

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": 1},
            "indexes": filter_indexes,
        },
    )
    result = execute_command(
        collection,
        {"explain": command_builder(collection.name), "verbosity": "queryPlanner"},
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
        {"indexFilterSet": Eq(True), "winningIndex": Eq(expected_index)},
        msg=f"filter should force {expected_index}",
        raw_res=True,
    )
