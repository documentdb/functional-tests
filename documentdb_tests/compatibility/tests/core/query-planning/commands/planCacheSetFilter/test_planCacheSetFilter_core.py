"""Tests for planCacheSetFilter core behavior and query shape semantics."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Len


# Property [Success Response]: planCacheSetFilter returns ok:1.0 on success.
SET_FILTER_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "success_response",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should return ok:1.0 on success",
    ),
    CommandTestCase(
        "empty_collection",
        docs=[],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should succeed on an empty collection",
    ),
]

# Property [Non-Existent Collection]: planCacheSetFilter rejects a non-existent collection.
SET_FILTER_NON_EXISTENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_existent_collection",
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject a non-existent collection",
    ),
]

SET_FILTER_ALL_TESTS: list[CommandTestCase] = (
    SET_FILTER_SUCCESS_TESTS + SET_FILTER_NON_EXISTENT_TESTS
)


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_ALL_TESTS))
def test_planCacheSetFilter_success(database_client, collection, test):
    """Test planCacheSetFilter success and error cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_planCacheSetFilter_query_only_shape(collection):
    """Test planCacheSetFilter sets a filter for a query-only shape."""
    collection.insert_one({"_id": 1, "status": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"status": 1},
        indexes=[{"status": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(1)},
        msg="planCacheListFilters should show the query-only shape filter",
        raw_res=True,
    )


def test_planCacheSetFilter_full_shape(collection):
    """Test planCacheSetFilter sets a filter for a full query shape."""
    collection.insert_one({"_id": 1, "item": 1, "date": 1, "qty": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"item": 1},
        sort={"date": 1},
        projection={"qty": 1},
        collation={"locale": "en"},
        indexes=[{"item": 1, "date": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(1)},
        msg="planCacheListFilters should return exactly 1 filter for full shape",
        raw_res=True,
    )


def test_planCacheSetFilter_override(collection):
    """Test planCacheSetFilter overrides existing filter for same shape."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        indexes=[{"a": 1}],
    )
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        indexes=[{"b": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(1)},
        msg="planCacheListFilters should show 1 filter after override",
        raw_res=True,
    )


def test_planCacheSetFilter_different_shapes_independent(collection):
    """Test different query shapes create independent filters."""
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

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(2)},
        msg="planCacheListFilters should show 2 independent filters",
        raw_res=True,
    )


def test_planCacheSetFilter_sort_creates_distinct_shape(collection):
    """Test adding sort to same query creates a different shape."""
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
        query={"a": 1},
        sort={"b": 1},
        indexes=[{"a": 1, "b": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(2)},
        msg="Sort should create a distinct shape (2 filters expected)",
        raw_res=True,
    )


def test_planCacheSetFilter_projection_creates_distinct_shape(collection):
    """Test adding projection to same query creates a different shape."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        indexes=[{"a": 1}],
    )
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        projection={"a": 1},
        indexes=[{"a": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(2)},
        msg="Projection should create a distinct shape (2 filters expected)",
        raw_res=True,
    )


def test_planCacheSetFilter_collation_creates_distinct_shape(collection):
    """Test adding collation to same query creates a different shape."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        indexes=[{"a": 1}],
    )
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        collation={"locale": "en"},
        indexes=[{"a": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {"filters": Len(2)},
        msg="Collation should create a distinct shape (2 filters expected)",
        raw_res=True,
    )


def test_planCacheSetFilter_list_filters_output_full(collection):
    """Test planCacheListFilters returns all shape fields after setting a filter."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        sort={"b": 1},
        projection={"c": 1},
        collation={"locale": "en"},
        indexes=[{"a": 1, "b": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {
            "filters": Len(1),
            "filters.0": {
                "query": Exists(),
                "sort": Exists(),
                "projection": Exists(),
                "indexes": Exists(),
            },
        },
        msg="planCacheListFilters should return all shape fields",
        raw_res=True,
    )


def test_planCacheSetFilter_list_filters_omitted_optional_fields(collection):
    """Test planCacheListFilters output when optional fields are omitted."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.database.command(
        "planCacheSetFilter",
        collection.name,
        query={"a": 1},
        indexes=[{"a": 1}],
    )

    list_result = execute_command(
        collection, {"planCacheListFilters": collection.name}
    )
    assertProperties(
        list_result,
        {
            "filters": Len(1),
            "filters.0": {
                "query": Eq({"a": 1}),
                "indexes": Eq([{"a": 1}]),
            },
        },
        msg="planCacheListFilters should show query and indexes for query-only filter",
        raw_res=True,
    )
