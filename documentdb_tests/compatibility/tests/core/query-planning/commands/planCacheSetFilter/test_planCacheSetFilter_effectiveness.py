"""Tests for planCacheSetFilter effectiveness via explain.

Verifies that index filters actually constrain plan selection, not just
that they are accepted and persisted.
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


def _explain_find(collection: Any, query: dict, hint: dict | None = None) -> Any:
    """Run explain for a find command and return the full explain result."""
    cmd: dict = {"find": collection.name, "filter": query}
    if hint is not None:
        cmd["hint"] = hint
    return execute_command(
        collection,
        {"explain": cmd, "verbosity": "queryPlanner"},
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
    allowed_indexes: list[str] | None = None,
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
    if allowed_indexes is not None:
        idx = _get_winning_index(wp)
        found = idx in allowed_indexes if idx else False
        assertProperties(
            {"in_set": found},
            {"in_set": Eq(True)},
            msg=f"{msg} — winning index {idx} must be in {allowed_indexes}",
            raw_res=True,
        )


pytestmark = pytest.mark.admin


# ---------------------------------------------------------------------------
# Property [Filter Forces Index]: The filter constrains plan selection to
# the specified index set.  Cases A and B use the same query shape with
# different filters; the winning plan must switch indexes accordingly.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filter_indexes,expected_index",
    [
        pytest.param([{"a": 1, "b": 1}], "a_1_b_1", id="forces_a_1_b_1"),
        pytest.param([{"a": 1, "c": 1}], "a_1_c_1", id="forces_a_1_c_1"),
    ],
)
def test_filter_forces_index(collection, filter_indexes, expected_index):
    """Test filter forces the specified index for query {a: 1}."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(10)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.create_index([("a", 1), ("c", 1)])

    _set_filter(collection, {"a": 1}, filter_indexes)
    result = _explain_find(collection, {"a": 1})

    _assert_explain(
        result,
        index_filter_set=True,
        expected_index=expected_index,
        msg=f"filter should force {expected_index} for query {{a: 1}}",
    )


# ---------------------------------------------------------------------------
# Property [Multiple Allowed Indexes]: When the filter allows multiple
# indexes, the winning plan must pick from that set.
# ---------------------------------------------------------------------------


def test_multiple_allowed_indexes(collection):
    """Test filter with multiple allowed indexes constrains to that set."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(10)])
    collection.create_index([("a", 1)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.create_index([("c", 1)])

    _set_filter(collection, {"a": 1, "b": 1}, [{"a": 1}, {"c": 1}])
    result = _explain_find(collection, {"a": 1, "b": 1})

    _assert_explain(
        result,
        index_filter_set=True,
        allowed_indexes=["a_1", "c_1"],
        msg="filter should constrain to {a_1, c_1}",
    )


# ---------------------------------------------------------------------------
# Property [Hint Overridden by Filter]: When a filter is active, a user-
# supplied hint is overridden.
# ---------------------------------------------------------------------------


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
    """Test filter overrides a conflicting user hint."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(10)])
    collection.create_index([("a", 1), ("b", 1)])
    collection.create_index([("a", 1), ("c", 1)])

    _set_filter(collection, {"a": 1}, filter_indexes)
    result = _explain_find(collection, {"a": 1}, hint=hint)

    _assert_explain(
        result,
        index_filter_set=True,
        expected_index=expected_index,
        msg=f"filter should override hint and force {expected_index}",
    )


# ---------------------------------------------------------------------------
# Property [COLLSCAN Fallback]: When the filter restricts to an index that
# cannot serve the query, the planner falls back to COLLSCAN.
# ---------------------------------------------------------------------------


def test_collscan_fallback(collection):
    """Test filter to unusable index forces COLLSCAN."""
    collection.insert_many([{"a": i} for i in range(10)])
    collection.create_index([("a", 1)])

    _set_filter(collection, {"a": 1}, [{"nonexistent_field": 1}])
    result = _explain_find(collection, {"a": 1})

    _assert_explain(
        result,
        index_filter_set=True,
        expected_stage="COLLSCAN",
        msg="filter to unusable index should force COLLSCAN",
    )


# ---------------------------------------------------------------------------
# Property [Filter Scoped to Exact Shape]: A filter for one query shape
# does not affect a different shape.
# ---------------------------------------------------------------------------


def test_filter_scoped_to_exact_shape(collection):
    """Test filter on {a: 1} does not affect shape {a: 1, b: 1}."""
    collection.insert_many([{"a": i, "b": i} for i in range(10)])
    collection.create_index([("a", 1)])
    collection.create_index([("b", 1)])

    _set_filter(collection, {"a": 1}, [{"b": 1}])

    # Filtered shape
    result_filtered = _explain_find(collection, {"a": 1})
    _assert_explain(
        result_filtered,
        index_filter_set=True,
        msg="indexFilterSet should be True for the filtered shape",
    )

    # Different shape — not affected
    result_unfiltered = _explain_find(collection, {"a": 1, "b": 1})
    _assert_explain(
        result_unfiltered,
        index_filter_set=False,
        msg="indexFilterSet should be False for a different shape",
    )
