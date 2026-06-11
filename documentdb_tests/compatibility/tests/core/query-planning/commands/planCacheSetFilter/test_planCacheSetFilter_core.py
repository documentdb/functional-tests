"""Tests for planCacheSetFilter core behavior and query shape semantics."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Len
from documentdb_tests.framework.target_collection import CappedCollection

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
    CommandTestCase(
        "full_shape",
        docs=[{"_id": 1, "item": 1, "date": 1, "qty": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"item": 1},
            "sort": {"date": 1},
            "projection": {"qty": 1},
            "collation": {"locale": "en"},
            "indexes": [{"item": 1, "date": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept a full shape with sort, projection, and collation",
    ),
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should succeed on a capped collection",
    ),
]

# Property [Query Predicates]: planCacheSetFilter accepts various query predicate forms.
SET_FILTER_QUERY_PREDICATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_query",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {},
            "indexes": [{"_id": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept an empty query document",
    ),
    CommandTestCase(
        "dot_notation",
        docs=[{"_id": 1, "a": {"b": 1}}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a.b": 1},
            "indexes": [{"a.b": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept dot-notation field paths in query",
    ),
    CommandTestCase(
        "comparison_operator",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": {"$gt": 5}},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept comparison operators in query",
    ),
    CommandTestCase(
        "multi_field_query",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1, "b": 2},
            "indexes": [{"a": 1, "b": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept multi-field query",
    ),
    CommandTestCase(
        "logical_operator",
        docs=[{"_id": 1, "a": 5, "b": 5}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"$and": [{"a": {"$gt": 1}}, {"b": {"$lt": 10}}]},
            "indexes": [{"a": 1, "b": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept logical operators in query",
    ),
]

# Property [Index Specification]: planCacheSetFilter accepts various index specification formats.
SET_FILTER_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "compound_index",
        docs=[{"_id": 1, "x": 1, "y": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"x": 1},
            "indexes": [{"x": 1, "y": -1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept a compound index specification",
    ),
    CommandTestCase(
        "multiple_indexes",
        docs=[{"_id": 1, "x": 1, "y": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"x": 1},
            "indexes": [{"x": 1}, {"y": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept multiple index specifications",
    ),
    CommandTestCase(
        "non_existent_index",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"nonexistent_field": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept a non-existent index specification",
    ),
    CommandTestCase(
        "descending_index",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": -1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept descending index specification",
    ),
    CommandTestCase(
        "large_compound_index",
        docs=[{"_id": 1, "a": 1, "b": 1, "c": 1, "d": 1, "e": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1, "b": 1, "c": 1, "d": 1, "e": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept a compound index with many fields",
    ),
    CommandTestCase(
        "duplicate_index_entries",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}, {"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept duplicate index entries",
    ),
    CommandTestCase(
        "many_indexes",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [
                {"a": 1},
                {"b": 1},
                {"c": 1},
                {"d": 1},
                {"e": 1},
                {"f": 1},
                {"g": 1},
                {"h": 1},
                {"i": 1},
                {"j": 1},
            ],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept many index specifications",
    ),
    CommandTestCase(
        "wildcard_index",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"$**": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept wildcard index specification",
    ),
]

# Property [Optional Field Edge Cases]: planCacheSetFilter accepts edge-case values for
# optional fields.
SET_FILTER_OPTIONAL_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "multi_field_sort",
        docs=[{"_id": 1, "a": 1, "b": 1, "c": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "sort": {"b": 1, "c": -1},
            "indexes": [{"a": 1, "b": 1, "c": -1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept multi-field sort",
    ),
    CommandTestCase(
        "sort_empty_document",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "sort": {},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept empty sort document",
    ),
    CommandTestCase(
        "projection_empty_document",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": {},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept empty projection document",
    ),
    CommandTestCase(
        "projection_inclusion",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": {"b": 1},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept inclusion projection",
    ),
    CommandTestCase(
        "projection_exclusion",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": {"b": 0},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept exclusion projection",
    ),
    CommandTestCase(
        "query_array",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": [],
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept array as query",
    ),
    CommandTestCase(
        "sort_array",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "sort": [],
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept array as sort",
    ),
    CommandTestCase(
        "projection_array",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": [],
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept array as projection",
    ),
]

# Property [Comment Field]: planCacheSetFilter accepts the comment field with any BSON type.
SET_FILTER_COMMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
            "comment": v,
        },
        expected={"ok": 1.0},
        msg=f"planCacheSetFilter should accept {type_id} as comment",
    )
    for type_id, value in [
        ("string", "a comment"),
        ("int32", 42),
        ("document", {"key": "value"}),
        ("array", [1, 2, 3]),
        ("bool_true", True),
        ("null", None),
    ]
]

# Property [Unrecognized Fields]: planCacheSetFilter silently accepts unrecognized fields.
SET_FILTER_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_field",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
            "unknownField": 1,
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should silently accept unrecognized fields",
    ),
]

SET_FILTER_CORE_TESTS: list[CommandTestCase] = (
    SET_FILTER_SUCCESS_TESTS
    + SET_FILTER_QUERY_PREDICATE_TESTS
    + SET_FILTER_INDEX_TESTS
    + SET_FILTER_OPTIONAL_EDGE_TESTS
    + SET_FILTER_COMMENT_TESTS
    + SET_FILTER_UNRECOGNIZED_FIELD_TESTS
)


# Property [Index By Name]: indexes can be specified as index name strings.
SET_FILTER_INDEX_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "index_by_name",
        docs=[{"_id": 1, "x": 1}],
        setup=lambda coll: coll.create_index("x"),
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"x": 1},
            "indexes": ["x_1"],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept index name string",
    ),
    CommandTestCase(
        "mixed_index_specs",
        docs=[{"_id": 1, "x": 1, "y": 1}],
        setup=lambda coll: coll.create_index("y"),
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"x": 1},
            "indexes": [{"x": 1}, "y_1"],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept mix of spec documents and name strings",
    ),
]

SET_FILTER_ALL_CORE_TESTS: list[CommandTestCase] = (
    SET_FILTER_CORE_TESTS + SET_FILTER_INDEX_NAME_TESTS
)


# Property [Query Shape Semantics]: planCacheSetFilter manages filters by query shape.
SET_FILTER_SHAPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_only_shape",
        docs=[{"_id": 1, "status": 1}],
        setup=lambda coll: execute_command(
            coll,
            {"planCacheSetFilter": coll.name, "query": {"status": 1}, "indexes": [{"status": 1}]},
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(1)},
        msg="planCacheListFilters should show the query-only shape filter",
    ),
    CommandTestCase(
        "full_shape_verification",
        docs=[{"_id": 1, "item": 1, "date": 1, "qty": 1}],
        setup=lambda coll: execute_command(
            coll,
            {
                "planCacheSetFilter": coll.name,
                "query": {"item": 1},
                "sort": {"date": 1},
                "projection": {"qty": 1},
                "collation": {"locale": "en"},
                "indexes": [{"item": 1, "date": 1}],
            },
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(1)},
        msg="planCacheListFilters should return exactly 1 filter for full shape",
    ),
    CommandTestCase(
        "override",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"b": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters": Len(1),
            "filters.0.indexes": Eq([{"b": 1}]),
        },
        msg="Setting the same shape twice should override with the latest indexes",
    ),
    CommandTestCase(
        "different_shapes_independent",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"b": 1}, "indexes": [{"b": 1}]},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(2)},
        msg="planCacheListFilters should show 2 independent filters",
    ),
    CommandTestCase(
        "sort_creates_distinct_shape",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "sort": {"a": 1},
                    "indexes": [{"a": 1}],
                },
            ),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "sort": {"a": -1},
                    "indexes": [{"a": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(2)},
        msg="Sort should create a distinct shape (2 filters expected)",
    ),
    CommandTestCase(
        "projection_creates_distinct_shape",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "projection": {"a": 1},
                    "indexes": [{"a": 1}],
                },
            ),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "projection": {"b": 1},
                    "indexes": [{"a": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(2)},
        msg="Projection should create a distinct shape (2 filters expected)",
    ),
    CommandTestCase(
        "collation_creates_distinct_shape",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "collation": {"locale": "en"},
                    "indexes": [{"a": 1}],
                },
            ),
            execute_command(
                coll,
                {
                    "planCacheSetFilter": coll.name,
                    "query": {"a": 1},
                    "collation": {"locale": "fr"},
                    "indexes": [{"a": 1}],
                },
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(2)},
        msg="Collation should create a distinct shape (2 filters expected)",
    ),
    CommandTestCase(
        "same_shape_different_value",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: (
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

# Property [ListFilters Output]: planCacheListFilters returns filter shape fields.
SET_FILTER_LIST_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "list_filters_output_full",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: execute_command(
            coll,
            {
                "planCacheSetFilter": coll.name,
                "query": {"a": 1},
                "sort": {"b": 1},
                "projection": {"c": 1},
                "collation": {"locale": "en"},
                "indexes": [{"a": 1, "b": 1}],
            },
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters": Len(1),
            "filters.0": {
                "query": Exists(),
                "sort": Exists(),
                "projection": Exists(),
                "indexes": Exists(),
            },
        },
        msg="planCacheListFilters should return all shape fields",
    ),
    CommandTestCase(
        "list_filters_omitted_optional",
        docs=[{"_id": 1, "a": 1}],
        setup=lambda coll: execute_command(
            coll,
            {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={
            "filters": Len(1),
            "filters.0": {
                "query": Eq({"a": 1}),
                "indexes": Eq([{"a": 1}]),
            },
        },
        msg="planCacheListFilters should show query and indexes for query-only filter",
    ),
]

SET_FILTER_SHAPE_ALL_TESTS: list[CommandTestCase] = (
    SET_FILTER_SHAPE_TESTS + SET_FILTER_LIST_OUTPUT_TESTS
)

SET_FILTER_ALL_TESTS: list[CommandTestCase] = SET_FILTER_ALL_CORE_TESTS + SET_FILTER_SHAPE_ALL_TESTS


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_ALL_TESTS))
def test_planCacheSetFilter(database_client, collection, test):
    """Test planCacheSetFilter core behavior and query shape semantics."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
