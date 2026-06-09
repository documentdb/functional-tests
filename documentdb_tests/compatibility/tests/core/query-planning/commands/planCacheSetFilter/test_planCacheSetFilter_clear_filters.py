"""Tests for planCacheSetFilter interaction with planCacheClearFilters."""

from __future__ import annotations

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Len


def test_planCacheSetFilter_clear_specific_filter(collection):
    """Test planCacheClearFilters removes only the matching filter."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        indexes=[{"a": 1}],
    )
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"b": 1},
        indexes=[{"b": 1}],
    )
    collection.database.command(
        "planCacheClearFilters",
        collection.name,
        query={"a": 1},
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(1)},
        msg="planCacheClearFilters should remove only the matching filter",
        raw_res=True,
    )


def test_planCacheSetFilter_clear_all_filters(collection):
    """Test planCacheClearFilters without query removes all filters."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        indexes=[{"a": 1}],
    )
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"b": 1},
        indexes=[{"b": 1}],
    )
    collection.database.command("planCacheClearFilters", collection.name)

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(0)},
        msg="planCacheClearFilters without query should remove all filters",
        raw_res=True,
    )
