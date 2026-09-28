"""Tests for planCacheClearFilters command behavioral verification.

Verifies that planCacheClearFilters actually removes index filters, not just
that it returns ok: 1.0. Uses planCacheSetFilter to establish filters and
planCacheListFilters to observe filter state before and after clearing.
"""

from __future__ import annotations

from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertNotError, assertSuccess
from documentdb_tests.framework.executor import execute_command


def _set_filters(collection: Collection) -> None:
    """Set two distinct index filters on the collection.

    Raises AssertionError if the filters are not visible via
    planCacheListFilters after being set.
    """
    collection.insert_many([{"_id": i, "a": i, "b": i % 5} for i in range(10)])
    collection.create_index("a")
    collection.create_index("b")

    db = collection.database
    db.command(
        {
            "planCacheSetFilter": collection.name,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        }
    )
    db.command(
        {
            "planCacheSetFilter": collection.name,
            "query": {"b": 1},
            "indexes": [{"b": 1}],
        }
    )

    list_result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertNotError(list_result, msg="planCacheListFilters precondition check")
    filters = list_result.get("filters", [])
    if len(filters) < 2:
        raise AssertionError(
            f"Precondition failed: expected at least 2 index filters "
            f"after setup, got {len(filters)}"
        )


# Property [Clear All Filters]: planCacheClearFilters without query shape
# parameters removes all index filters for the collection.
def test_planCacheClearFilters_clears_all_filters(collection: Collection):
    """Test planCacheClearFilters removes all index filters."""
    _set_filters(collection)

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
    _set_filters(collection)

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
