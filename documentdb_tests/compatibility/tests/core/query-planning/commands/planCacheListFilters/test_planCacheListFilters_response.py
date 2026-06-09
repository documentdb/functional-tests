"""Tests for planCacheListFilters response structure and filter content."""

from __future__ import annotations

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import (
    ContainsElement,
    Eq,
    Exists,
    IsType,
    Len,
)


def _set_filter(collection, **kwargs):
    """Set an index filter via planCacheSetFilter (test setup)."""
    cmd = {"planCacheSetFilter": collection.name, **kwargs}
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, {"ok": 1.0}, msg="planCacheSetFilter setup should succeed")


# Property [Ok Field Type]: planCacheListFilters ok field is of type double.
def test_planCacheListFilters_ok_type(collection):
    """Test planCacheListFilters ok field is of type double."""
    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"ok": IsType("double")},
        msg="planCacheListFilters ok field should be of type double",
        raw_res=True,
    )


# Property [Filters Field Type]: planCacheListFilters filters field is of
# type array even when empty.
def test_planCacheListFilters_filters_type(collection):
    """Test planCacheListFilters filters field is of type array."""
    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters": IsType("array")},
        msg="planCacheListFilters filters field should be of type array",
        raw_res=True,
    )


# Property [Single Filter Entry]: after setting one filter, the response
# contains one entry with matching query, sort, projection, and indexes.
def test_planCacheListFilters_single_filter(collection):
    """Test planCacheListFilters returns a single filter entry after planCacheSetFilter."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {
            "filters": Len(1),
            "filters.0.query": Eq({"a": 1}),
            "filters.0.indexes": Eq([{"a": 1}]),
        },
        msg="planCacheListFilters should return one filter entry with matching query and indexes",
        raw_res=True,
    )


# Property [Default Sort]: filter entry sort is empty document when sort was
# not specified in planCacheSetFilter.
def test_planCacheListFilters_default_sort(collection):
    """Test planCacheListFilters filter entry sort defaults to empty document."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters.0.sort": Eq({})},
        msg="planCacheListFilters should default sort to empty document",
        raw_res=True,
    )


# Property [Default Projection]: filter entry projection is empty document
# when projection was not specified in planCacheSetFilter.
def test_planCacheListFilters_default_projection(collection):
    """Test planCacheListFilters filter entry projection defaults to empty document."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters.0.projection": Eq({})},
        msg="planCacheListFilters should default projection to empty document",
        raw_res=True,
    )


# Property [Sort In Entry]: after setting a filter with sort, the filter
# entry includes the sort document.
def test_planCacheListFilters_with_sort(collection):
    """Test planCacheListFilters returns sort in filter entry."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1, "b": 1})
    _set_filter(collection, query={"a": 1}, sort={"b": 1}, indexes=[{"a": 1, "b": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters.0.sort": Eq({"b": 1})},
        msg="planCacheListFilters should return sort matching planCacheSetFilter",
        raw_res=True,
    )


# Property [Projection In Entry]: after setting a filter with projection,
# the filter entry includes the projection document.
def test_planCacheListFilters_with_projection(collection):
    """Test planCacheListFilters returns projection in filter entry."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, projection={"a": 1}, indexes=[{"a": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters.0.projection": Eq({"a": 1})},
        msg="planCacheListFilters should return projection matching planCacheSetFilter",
        raw_res=True,
    )


# Property [Collation In Entry]: after setting a filter with collation, the
# filter entry includes the collation document.
def test_planCacheListFilters_with_collation(collection):
    """Test planCacheListFilters returns collation in filter entry."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, collation={"locale": "en"}, indexes=[{"a": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {
            "filters.0.collation": Exists(),
            "filters.0.collation.locale": Eq("en"),
        },
        msg="planCacheListFilters should return collation with locale en",
        raw_res=True,
    )


# Property [Full Collation In Entry]: after setting a filter with full
# collation, all collation fields are returned.
def test_planCacheListFilters_with_full_collation(collection):
    """Test planCacheListFilters returns full collation document in filter entry."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(
        collection,
        query={"a": 1},
        collation={"locale": "fr", "strength": 2},
        indexes=[{"a": 1}],
    )

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {
            "filters.0.collation.locale": Eq("fr"),
            "filters.0.collation.strength": Eq(2),
        },
        msg="planCacheListFilters should return collation with locale fr and strength 2",
        raw_res=True,
    )


# Property [All Shape Parameters]: after setting a filter with all shape
# parameters, all fields are present in the filter entry.
def test_planCacheListFilters_all_shape_params(collection):
    """Test planCacheListFilters returns all shape parameters in filter entry."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1})
    _set_filter(
        collection,
        query={"a": 1},
        sort={"b": 1},
        projection={"a": 1},
        collation={"locale": "en"},
        indexes=[{"a": 1}],
    )

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {
            "filters.0.query": Eq({"a": 1}),
            "filters.0.sort": Eq({"b": 1}),
            "filters.0.projection": Eq({"a": 1}),
            "filters.0.collation": Exists(),
            "filters.0.indexes": Eq([{"a": 1}]),
        },
        msg="planCacheListFilters should return all shape parameters in filter entry",
        raw_res=True,
    )


# Property [Multiple Indexes]: filter entry indexes field contains all
# indexes specified in planCacheSetFilter.
def test_planCacheListFilters_multiple_indexes(collection):
    """Test planCacheListFilters returns multiple indexes in filter entry."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index({"a": 1})
    collection.create_index({"a": 1, "b": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}, {"a": 1, "b": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters.0.indexes": Len(2)},
        msg="planCacheListFilters should return both specified indexes",
        raw_res=True,
    )


# Property [Filter Entry Field Types]: query, sort, projection are documents
# and indexes is an array.
def test_planCacheListFilters_entry_field_types(collection):
    """Test planCacheListFilters filter entry field types."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {
            "filters.0.query": IsType("object"),
            "filters.0.sort": IsType("object"),
            "filters.0.projection": IsType("object"),
            "filters.0.indexes": IsType("array"),
        },
        msg="planCacheListFilters filter entry fields should have correct types",
        raw_res=True,
    )


# Property [Index By Name]: after setting a filter with index specified by
# name, the name is returned in the indexes array.
def test_planCacheListFilters_index_by_name(collection):
    """Test planCacheListFilters returns index name when set by name."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1}, name="a_1")
    _set_filter(collection, query={"a": 1}, indexes=["a_1"])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters.0.indexes": ContainsElement("a_1")},
        msg="planCacheListFilters should return index name in indexes array",
        raw_res=True,
    )


# Property [Index By Key Pattern]: after setting a filter with index
# specified by key pattern, the key pattern is returned in the indexes array.
def test_planCacheListFilters_index_by_key_pattern(collection):
    """Test planCacheListFilters returns key pattern when set by key pattern."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index({"a": 1})
    _set_filter(collection, query={"a": 1}, indexes=[{"a": 1}])

    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertProperties(
        result,
        {"filters.0.indexes": ContainsElement({"a": 1})},
        msg="planCacheListFilters should return key pattern in indexes array",
        raw_res=True,
    )
