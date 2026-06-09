"""Tests for planCacheListFilters filter lifecycle and integration."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len


def _setup_filter(collection, **kwargs):
    """Set an index filter via planCacheSetFilter."""
    result = execute_command(collection, {"planCacheSetFilter": collection.name, **kwargs})
    assert result["ok"] == 1.0, "planCacheSetFilter setup should succeed"


def _clear_filters(collection, **kwargs):
    """Clear index filters via planCacheClearFilters."""
    result = execute_command(collection, {"planCacheClearFilters": collection.name, **kwargs})
    assert result["ok"] == 1.0, "planCacheClearFilters setup should succeed"


# Property [Multiple Filters — Two Shapes]: planCacheListFilters returns both
# filters when two different query shapes are set.
LIST_FILTERS_MULTIPLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "two_shapes",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            coll.create_index({"b": 1}),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1}]),
            _setup_filter(coll, query={"b": 1}, indexes=[{"b": 1}]),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(2)},
        msg="planCacheListFilters should return 2 filters for 2 query shapes",
    ),
    CommandTestCase(
        "three_shapes",
        docs=[{"_id": 1, "a": 1, "b": 1, "c": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            coll.create_index({"b": 1}),
            coll.create_index({"c": 1}),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1}]),
            _setup_filter(coll, query={"b": 1}, indexes=[{"b": 1}]),
            _setup_filter(coll, query={"c": 1}, indexes=[{"c": 1}]),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(3)},
        msg="planCacheListFilters should return 3 filters for 3 query shapes",
    ),
]

# Property [Filter Override]: re-setting a filter for the same query shape
# overrides the previous indexes.
LIST_FILTERS_OVERRIDE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "override_indexes",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            coll.create_index({"a": 1, "b": 1}),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1}]),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1, "b": 1}]),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters": Len(1),
            "filters.0.indexes": Eq([{"a": 1, "b": 1}]),
        },
        msg="planCacheListFilters should have 1 filter with overridden indexes",
    ),
]

# Property [Lifecycle — Empty Before Set]: planCacheListFilters returns empty
# filters before any filters are set.
LIST_FILTERS_EMPTY_BEFORE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_before_set",
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Eq([]), "ok": Eq(1.0)},
        msg="planCacheListFilters should return empty filters initially",
    ),
]

# Property [Lifecycle — Present After Set]: planCacheListFilters returns the
# filter after planCacheSetFilter is called.
LIST_FILTERS_PRESENT_AFTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "present_after_set",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1}]),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(1)},
        msg="planCacheListFilters should have 1 filter after set",
    ),
]

# Property [Lifecycle — Empty After Clear All]: planCacheListFilters returns
# empty filters after planCacheClearFilters clears all filters.
LIST_FILTERS_CLEAR_ALL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_after_clear_all",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1}]),
            _clear_filters(coll),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Eq([]), "ok": Eq(1.0)},
        msg="planCacheListFilters should return empty filters after clear all",
    ),
]

# Property [Lifecycle — Remaining After Selective Clear]: after clearing one
# query shape, the remaining filter is still returned.
LIST_FILTERS_SELECTIVE_CLEAR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "remaining_after_selective_clear",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            coll.create_index({"b": 1}),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1}]),
            _setup_filter(coll, query={"b": 1}, indexes=[{"b": 1}]),
            _clear_filters(coll, query={"a": 1}),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters": Len(1),
            "filters.0.query": Eq({"b": 1}),
        },
        msg="planCacheListFilters should have 1 remaining filter for query {b: 1}",
    ),
]

# Property [Index Lifecycle]: filters persist even after the referenced
# index is dropped.
LIST_FILTERS_INDEX_DROPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "index_dropped",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}, name="a_1"),
            _setup_filter(coll, query={"a": 1}, indexes=[{"a": 1}]),
            coll.drop_index("a_1"),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters": Len(1),
            "filters.0.query": Eq({"a": 1}),
        },
        msg="planCacheListFilters should still return filter after index is dropped",
    ),
]

LIST_FILTERS_LIFECYCLE_TESTS: list[CommandTestCase] = (
    LIST_FILTERS_MULTIPLE_TESTS
    + LIST_FILTERS_OVERRIDE_TESTS
    + LIST_FILTERS_EMPTY_BEFORE_TESTS
    + LIST_FILTERS_PRESENT_AFTER_TESTS
    + LIST_FILTERS_CLEAR_ALL_TESTS
    + LIST_FILTERS_SELECTIVE_CLEAR_TESTS
    + LIST_FILTERS_INDEX_DROPPED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(LIST_FILTERS_LIFECYCLE_TESTS))
def test_planCacheListFilters_lifecycle(database_client, collection, test):
    """Test planCacheListFilters filter lifecycle and integration."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertProperties(result, test.build_expected(ctx), msg=test.msg, raw_res=True)


# Property [Collection Isolation]: filters set on collection A are not
# visible when listing filters on collection B.
def test_planCacheListFilters_collection_isolation(database_client, collection):
    """Test planCacheListFilters is scoped to the specific collection."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _setup_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    other_coll = database_client.create_collection(f"{collection.name}_other")
    try:
        result = execute_command(other_coll, {"planCacheListFilters": other_coll.name})
        assertResult(
            result,
            expected={"filters": [], "ok": 1.0},
            msg="planCacheListFilters should not show filters from another collection",
            raw_res=True,
        )
    finally:
        database_client.drop_collection(other_coll.name)
