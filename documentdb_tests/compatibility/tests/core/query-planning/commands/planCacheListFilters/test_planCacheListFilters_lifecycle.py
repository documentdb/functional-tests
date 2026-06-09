"""Tests for planCacheListFilters filter lifecycle and integration."""

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len


def _set_filter(collection, **kwargs):
    """Set an index filter via planCacheSetFilter."""
    cmd = {"planCacheSetFilter": collection.name, **kwargs}
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, {"ok": 1.0}, msg="planCacheSetFilter setup should succeed")


def _clear_filters(collection, **kwargs):
    """Clear index filters via planCacheClearFilters."""
    cmd = {"planCacheClearFilters": collection.name, **kwargs}
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, {"ok": 1.0}, msg="planCacheClearFilters setup should succeed")


def _list_filters(collection):
    """Run planCacheListFilters and return the raw result."""
    return execute_command(collection, {"planCacheListFilters": collection.name})


# Property [Multiple Filters — Two Shapes]: planCacheListFilters returns both
# filters when two different query shapes are set.
def test_planCacheListFilters_two_shapes(collection):
    """Test planCacheListFilters returns two filters for two query shapes."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1})
    collection.create_index({"b": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    _set_filter(collection, query={"b": 1}, indexes=[{"b": 1}])

    result = _list_filters(collection)
    assertProperties(
        result,
        {
            "filters": Len(2),
        },
        msg="should return 2 filters for 2 query shapes",
        raw_res=True,
    )


# Property [Multiple Filters — Three Shapes]: planCacheListFilters returns
# all three filters when three different query shapes are set.
def test_planCacheListFilters_three_shapes(collection):
    """Test planCacheListFilters returns three filters for three query shapes."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1, "c": 1})
    collection.create_index({"a": 1})
    collection.create_index({"b": 1})
    collection.create_index({"c": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    _set_filter(collection, query={"b": 1}, indexes=[{"b": 1}])
    _set_filter(collection, query={"c": 1}, indexes=[{"c": 1}])

    result = _list_filters(collection)
    assertProperties(
        result,
        {"filters": Len(3)},
        msg="should return 3 filters for 3 query shapes",
        raw_res=True,
    )


# Property [Filter Count Matches Set Count]: the number of filter entries
# matches the number of distinct query shapes set.
def test_planCacheListFilters_count_matches(collection):
    """Test planCacheListFilters filter count matches set count."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1})
    collection.create_index({"b": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    _set_filter(collection, query={"b": 1}, indexes=[{"b": 1}])

    result = _list_filters(collection)
    assertProperties(
        result,
        {"filters": Len(2)},
        msg="filter count should match set count (2)",
        raw_res=True,
    )


# Property [Filter Override]: re-setting a filter for the same query shape
# overrides the previous indexes.
def test_planCacheListFilters_override(collection):
    """Test planCacheListFilters reflects overridden filter indexes."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1})
    collection.create_index({"a": 1, "b": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1, "b": 1}])

    result = _list_filters(collection)
    assertProperties(
        result,
        {
            "filters": Len(1),
            "filters.0.indexes": Eq([{"a": 1, "b": 1}]),
        },
        msg="should have 1 filter with overridden indexes",
        raw_res=True,
    )


# Property [Lifecycle — Empty Before Set]: planCacheListFilters returns empty
# filters before any filters are set.
def test_planCacheListFilters_empty_before_set(collection):
    """Test planCacheListFilters returns empty filters before any are set."""
    result = _list_filters(collection)
    assertSuccessPartial(
        result,
        {"filters": [], "ok": 1.0},
        msg="planCacheListFilters should return empty filters initially",
    )


# Property [Lifecycle — Present After Set]: planCacheListFilters returns the
# filter after planCacheSetFilter is called.
def test_planCacheListFilters_present_after_set(collection):
    """Test planCacheListFilters returns filter after set."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    result = _list_filters(collection)
    assertProperties(
        result,
        {"filters": Len(1)},
        msg="should have 1 filter after set",
        raw_res=True,
    )


# Property [Lifecycle — Empty After Clear All]: planCacheListFilters returns
# empty filters after planCacheClearFilters clears all filters.
def test_planCacheListFilters_empty_after_clear_all(collection):
    """Test planCacheListFilters returns empty filters after clearing all."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    _clear_filters(collection)

    result = _list_filters(collection)
    assertSuccessPartial(
        result,
        {"filters": [], "ok": 1.0},
        msg="planCacheListFilters should return empty filters after clear all",
    )


# Property [Lifecycle — Remaining After Selective Clear]: after clearing one
# query shape, the remaining filter is still returned.
def test_planCacheListFilters_remaining_after_selective_clear(collection):
    """Test planCacheListFilters returns remaining filter after selective clear."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1})
    collection.create_index({"b": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    _set_filter(collection, query={"b": 1}, indexes=[{"b": 1}])
    _clear_filters(collection, query={"a": 1})

    result = _list_filters(collection)
    assertProperties(
        result,
        {
            "filters": Len(1),
            "filters.0.query": Eq({"b": 1}),
        },
        msg="should have 1 remaining filter for query {b: 1}",
        raw_res=True,
    )


# Property [Lifecycle — Override Reflected]: planCacheListFilters reflects
# overridden filter when set twice with the same query shape.
def test_planCacheListFilters_lifecycle_override(collection):
    """Test planCacheListFilters reflects filter override in lifecycle."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1})
    collection.create_index({"a": 1, "b": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1, "b": 1}])

    result = _list_filters(collection)
    assertProperties(
        result,
        {
            "filters": Len(1),
            "filters.0.indexes": Eq([{"a": 1, "b": 1}]),
        },
        msg="should reflect overridden indexes",
        raw_res=True,
    )


# Property [Collection Isolation]: filters set on collection A are not
# visible when listing filters on collection B.
def test_planCacheListFilters_collection_isolation(database_client, collection):
    """Test planCacheListFilters is scoped to the specific collection."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    other_coll = database_client.create_collection(f"{collection.name}_other")
    try:
        result = execute_command(other_coll, {"planCacheListFilters": other_coll.name})
        assertSuccessPartial(
            result,
            {"filters": [], "ok": 1.0},
            msg="Filters on collection A should not appear on collection B",
        )
    finally:
        database_client.drop_collection(other_coll.name)


# Property [Index Lifecycle]: filters persist even after the referenced
# index is dropped.
def test_planCacheListFilters_index_dropped(collection):
    """Test planCacheListFilters still returns filter after index is dropped."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1}, name="a_1")
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])
    collection.drop_index("a_1")

    result = _list_filters(collection)
    assertProperties(
        result,
        {
            "filters": Len(1),
            "filters.0.query": Eq({"a": 1}),
        },
        msg="filter should persist after index is dropped",
        raw_res=True,
    )
