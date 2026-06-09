"""Tests for planCacheSetFilter core behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
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
        msg="planCacheSetFilter should accept a full shape with query, sort, projection, and collation",
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
]

# Property [Index Specification]: planCacheSetFilter accepts various index specification formats.
SET_FILTER_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_index",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"x": 1},
            "indexes": [{"x": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept a single index specification",
    ),
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

# Property [Optional Field Edge Cases]: planCacheSetFilter accepts edge-case values for optional fields.
SET_FILTER_OPTIONAL_EDGE_TESTS: list[CommandTestCase] = [
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


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_CORE_TESTS))
def test_planCacheSetFilter_cases(database_client, collection, test):
    """Test planCacheSetFilter cases."""
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


def test_planCacheSetFilter_index_by_name(collection):
    """Test planCacheSetFilter accepts index name strings."""
    collection.insert_one({"_id": 1, "x": 1})
    collection.create_index("x")

    result = execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"x": 1},
            "indexes": ["x_1"],
        },
    )
    assertResult(
        result,
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept index name string",
        raw_res=True,
    )


def test_planCacheSetFilter_mixed_index_specs(collection):
    """Test planCacheSetFilter accepts mix of spec documents and name strings."""
    collection.insert_one({"_id": 1, "x": 1, "y": 1})
    collection.create_index("y")

    result = execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": {"x": 1},
            "indexes": [{"x": 1}, "y_1"],
        },
    )
    assertResult(
        result,
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept mix of spec documents and name strings",
        raw_res=True,
    )
