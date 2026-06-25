"""Tests for planCacheSetFilter effectiveness via explain.

Verifies that index filters actually constrain plan selection, not just
that they are accepted and persisted.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


# Property [Filter Forces Index]: the filter constrains plan selection to the specified index set.
@pytest.mark.parametrize(
    "filter_indexes,expected_index",
    [
        pytest.param([{"a": 1, "b": 1}], "a_1_b_1", id="forces_a_1_b_1"),
        pytest.param([{"a": 1, "c": 1}], "a_1_c_1", id="forces_a_1_c_1"),
    ],
)
def test_filter_forces_index(collection, filter_indexes, expected_index):
    """Test planCacheSetFilter forces the specified index for query {a: 1}."""
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
        {
            "explain": {"find": collection.name, "filter": {"a": 1}},
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
        {"indexFilterSet": Eq(True), "winningIndex": Eq(expected_index)},
        msg=f"filter should force {expected_index} for query {{a: 1}}",
        raw_res=True,
    )


# Property [Multiple Allowed Indexes]: the winning plan must pick from the allowed set.
def test_multiple_allowed_indexes(collection):
    """Test planCacheSetFilter with multiple allowed indexes constrains to that set."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(10)])
    collection.create_index([("a", 1)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.create_index([("c", 1)])

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": 1, "b": 1},
            "indexes": [{"a": 1}, {"c": 1}],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": {"a": 1, "b": 1}},
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

    allowed = ["a_1", "c_1"]
    assertProperties(
        {
            "indexFilterSet": qp["indexFilterSet"],
            "inAllowedSet": winning_index in allowed if winning_index else False,
        },
        {"indexFilterSet": Eq(True), "inAllowedSet": Eq(True)},
        msg=f"filter should constrain to {allowed}",
        raw_res=True,
    )


# Property [Hint Overridden by Filter]: when a filter is active, a user-supplied hint is overridden.
@pytest.mark.parametrize(
    "filter_indexes,hint,expected_index",
    [
        pytest.param(
            [{"a": 1, "b": 1}],
            {"a": 1, "c": 1},
            "a_1_b_1",
            id="filter_b_overrides_hint_c",
        ),
        pytest.param(
            [{"a": 1, "c": 1}],
            {"a": 1, "b": 1},
            "a_1_c_1",
            id="filter_c_overrides_hint_b",
        ),
    ],
)
def test_hint_overridden_by_filter(collection, filter_indexes, hint, expected_index):
    """Test planCacheSetFilter overrides a conflicting user hint."""
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
        {
            "explain": {"find": collection.name, "filter": {"a": 1}, "hint": hint},
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
        {"indexFilterSet": Eq(True), "winningIndex": Eq(expected_index)},
        msg=f"filter should override hint and force {expected_index}",
        raw_res=True,
    )


# Property [COLLSCAN Fallback]: when the filter restricts to an unusable
# index, the planner falls back to COLLSCAN.
def test_collscan_fallback(collection):
    """Test planCacheSetFilter to unusable index forces COLLSCAN."""
    collection.insert_many([{"a": i} for i in range(10)])
    collection.create_index([("a", 1)])

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": 1},
            "indexes": [{"nonexistent_field": 1}],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": {"a": 1}},
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
        msg="filter to unusable index should force COLLSCAN",
        raw_res=True,
    )


# Property [Filter Scoped to Exact Shape]: a filter for one query shape
# does not affect a different shape.
@pytest.mark.parametrize(
    "query,expected_filter_set",
    [
        pytest.param({"a": 1}, True, id="filtered_shape"),
        pytest.param({"a": 1, "b": 1}, False, id="different_shape"),
    ],
)
def test_filter_scoped_to_exact_shape(collection, query, expected_filter_set):
    """Test planCacheSetFilter on {a: 1} only affects that exact shape."""
    collection.insert_many([{"a": i, "b": i} for i in range(10)])
    collection.create_index([("a", 1)])
    collection.create_index([("b", 1)])

    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": 1},
            "indexes": [{"b": 1}],
        },
    )

    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": query},
            "verbosity": "queryPlanner",
        },
    )
    assertProperties(
        {"indexFilterSet": result["queryPlanner"]["indexFilterSet"]},
        {"indexFilterSet": Eq(expected_filter_set)},
        msg=f"indexFilterSet should be {expected_filter_set} for query {query}",
        raw_res=True,
    )
