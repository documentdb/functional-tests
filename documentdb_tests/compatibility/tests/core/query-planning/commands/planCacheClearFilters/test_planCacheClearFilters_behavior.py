"""Tests for planCacheClearFilters command behavioral verification.

Verifies that planCacheClearFilters actually removes index filters, not just
that it returns ok: 1.0. Uses planCacheSetFilter to establish filters and
planCacheListFilters to observe filter state before and after clearing.
"""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def _set_filters(collection: Collection) -> Any:
    """Set two distinct index filters on the collection.

    Returns the engine error if a setup command fails, so the caller can
    forward it to the test's single assertion, or None on success. Raises
    AssertionError if the commands succeed but the filters are not visible
    via planCacheListFilters, since the test would then prove nothing.
    """
    collection.insert_many([{"_id": i, "a": i, "b": i % 5} for i in range(10)])
    collection.create_index("a")
    collection.create_index("b")

    for field in ("a", "b"):
        set_result = execute_command(
            collection,
            {
                "planCacheSetFilter": collection.name,
                "query": {field: 1},
                "indexes": [{field: 1}],
            },
        )
        if isinstance(set_result, Exception):
            return set_result

    list_result = execute_command(collection, {"planCacheListFilters": collection.name})
    if isinstance(list_result, Exception):
        return list_result
    filters = list_result.get("filters", [])
    if len(filters) < 2:
        raise AssertionError(
            f"Precondition failed: expected at least 2 index filters "
            f"after setup, got {len(filters)}"
        )
    return None


# Property [Clear All Filters]: planCacheClearFilters without query shape
# parameters removes all index filters for the collection.
def test_planCacheClearFilters_clears_all_filters(collection: Collection):
    """Test planCacheClearFilters removes all index filters."""
    result = _set_filters(collection)
    if result is None:
        execute_command(collection, {"planCacheClearFilters": collection.name})
        result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertSuccess(
        result,
        {"filters": [], "ok": 1.0},
        msg="All index filters should be removed after planCacheClearFilters",
        raw_res=True,
    )


# Property [Targeted Clear]: planCacheClearFilters with a query shape removes
# only the matching filter and leaves other filters intact.
def test_planCacheClearFilters_targeted_preserves_other_filters(collection: Collection):
    """Test planCacheClearFilters with query shape leaves non-targeted filters."""
    result = _set_filters(collection)
    if result is None:
        execute_command(
            collection,
            {"planCacheClearFilters": collection.name, "query": {"a": 1}},
        )
        result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertSuccess(
        result,
        {
            "filters": [
                {
                    "query": {"b": 1},
                    "sort": {},
                    "projection": {},
                    "indexes": [{"b": 1}],
                }
            ],
            "ok": 1.0,
        },
        msg="Only the non-targeted filter should remain after targeted planCacheClearFilters",
        raw_res=True,
    )
