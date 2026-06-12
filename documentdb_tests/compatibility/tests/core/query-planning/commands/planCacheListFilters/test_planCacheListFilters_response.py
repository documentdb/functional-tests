"""Tests for planCacheListFilters response structure and filter content."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    ContainsElement,
    Eq,
    Exists,
    IsType,
    Len,
)

# Property [Ok Field Type]: planCacheListFilters ok field is of type double.
LIST_FILTERS_OK_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ok_type_double",
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"ok": IsType("double")},
        msg="planCacheListFilters ok field should be of type double",
    ),
]

# Property [Filters Field Type]: planCacheListFilters filters field is of
# type array even when empty.
LIST_FILTERS_ARRAY_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "filters_type_array",
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": IsType("array")},
        msg="planCacheListFilters filters field should be of type array",
    ),
]

# Property [Single Filter Entry]: after setting one filter, the response
# contains one entry with matching query, sort, projection, and indexes.
LIST_FILTERS_SINGLE_ENTRY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_filter_entry",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters": Len(1),
            "filters.0.query": Eq({"a": 1}),
            "filters.0.indexes": Eq([{"a": 1}]),
        },
        msg="planCacheListFilters should return one filter entry with matching query and indexes",
    ),
    CommandTestCase(
        "same_shape_different_value",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 999}, "indexes": [{"a": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(1)},
        msg="planCacheListFilters should return 1 filter when queries differ only in value",
    ),
]

# Property [Default Sort]: filter entry sort is empty document when sort was
# not specified in planCacheSetFilter.
# Property [Default Projection]: filter entry projection is empty document
# when projection was not specified in planCacheSetFilter.
LIST_FILTERS_DEFAULTS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "default_sort",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters.0.sort": Eq({})},
        msg="planCacheListFilters should default sort to empty document",
    ),
    CommandTestCase(
        "default_projection",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters.0.projection": Eq({})},
        msg="planCacheListFilters should default projection to empty document",
    ),
]

# Property [Sort In Entry]: after setting a filter with sort, the filter
# entry includes the sort document.
# Property [Projection In Entry]: after setting a filter with projection,
# the filter entry includes the projection document.
LIST_FILTERS_SHAPE_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_in_entry",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1, "b": 1}),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "sort": {"b": 1},
                    "indexes": [{"a": 1, "b": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters.0.sort": Eq({"b": 1})},
        msg="planCacheListFilters should return sort matching planCacheSetFilter",
    ),
    CommandTestCase(
        "projection_in_entry",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "projection": {"a": 1},
                    "indexes": [{"a": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters.0.projection": Eq({"a": 1})},
        msg="planCacheListFilters should return projection matching planCacheSetFilter",
    ),
]

# Property [Collation In Entry]: after setting a filter with collation, the
# filter entry includes the collation document.
LIST_FILTERS_COLLATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_basic",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "collation": {"locale": "en"},
                    "indexes": [{"a": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters.0.collation": Exists(),
            "filters.0.collation.locale": Eq("en"),
        },
        msg="planCacheListFilters should return collation with locale en",
    ),
    CommandTestCase(
        "collation_full",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "collation": {"locale": "fr", "strength": 2},
                    "indexes": [{"a": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters.0.collation.locale": Eq("fr"),
            "filters.0.collation.strength": Eq(2),
        },
        msg="planCacheListFilters should return collation with locale fr and strength 2",
    ),
]

# Property [All Shape Parameters]: after setting a filter with all shape
# parameters, all fields are present in the filter entry.
LIST_FILTERS_ALL_PARAMS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_shape_params",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "sort": {"b": 1},
                    "projection": {"a": 1},
                    "collation": {"locale": "en"},
                    "indexes": [{"a": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters.0.query": Eq({"a": 1}),
            "filters.0.sort": Eq({"b": 1}),
            "filters.0.projection": Eq({"a": 1}),
            "filters.0.collation": Exists(),
            "filters.0.indexes": Eq([{"a": 1}]),
        },
        msg="planCacheListFilters should return all shape parameters in filter entry",
    ),
]

# Property [Multiple Indexes]: filter entry indexes field contains all
# indexes specified in planCacheSetFilter.
LIST_FILTERS_MULTI_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "entry_indexes_contains_all_specified",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            coll.create_index({"a": 1, "b": 1}),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "indexes": [{"a": 1}, {"a": 1, "b": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters.0.indexes": Len(2)},
        msg="planCacheListFilters should return both specified indexes",
    ),
]

# Property [Filter Entry Field Types]: query, sort, projection are documents
# and indexes is an array.
LIST_FILTERS_ENTRY_TYPES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "entry_fields_have_correct_types",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters.0.query": IsType("object"),
            "filters.0.sort": IsType("object"),
            "filters.0.projection": IsType("object"),
            "filters.0.indexes": IsType("array"),
        },
        msg="planCacheListFilters filter entry fields should have correct types",
    ),
]

# Property [Index By Name]: after setting a filter with index specified by
# name, the name is returned in the indexes array.
# Property [Index By Key Pattern]: after setting a filter with index
# specified by key pattern, the key pattern is returned in the indexes array.
LIST_FILTERS_INDEX_SPEC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "index_by_name",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}, name="a_1"),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": ["a_1"]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters.0.indexes": ContainsElement("a_1")},
        msg="planCacheListFilters should return index name in indexes array",
    ),
    CommandTestCase(
        "index_by_key_pattern",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            coll.create_index({"a": 1}),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters.0.indexes": ContainsElement({"a": 1})},
        msg="planCacheListFilters should return key pattern in indexes array",
    ),
]

LIST_FILTERS_RESPONSE_TESTS: list[CommandTestCase] = (
    LIST_FILTERS_OK_TYPE_TESTS
    + LIST_FILTERS_ARRAY_TYPE_TESTS
    + LIST_FILTERS_SINGLE_ENTRY_TESTS
    + LIST_FILTERS_DEFAULTS_TESTS
    + LIST_FILTERS_SHAPE_FIELDS_TESTS
    + LIST_FILTERS_COLLATION_TESTS
    + LIST_FILTERS_ALL_PARAMS_TESTS
    + LIST_FILTERS_MULTI_INDEX_TESTS
    + LIST_FILTERS_ENTRY_TYPES_TESTS
    + LIST_FILTERS_INDEX_SPEC_TESTS
)


@pytest.mark.parametrize("test", pytest_params(LIST_FILTERS_RESPONSE_TESTS))
def test_planCacheListFilters_response(database_client, collection, test):
    """Test planCacheListFilters response structure and filter content."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertProperties(result, test.build_expected(ctx), msg=test.msg, raw_res=True)
