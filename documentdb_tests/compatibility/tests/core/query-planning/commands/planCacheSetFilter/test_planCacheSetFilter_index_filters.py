"""Tests for planCacheSetFilter index filter specification and edge cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


# Property [Index as Specification Document]: indexes can be specified as index specification documents.
# Property [Index Variants]: planCacheSetFilter accepts various index specification formats.
SET_FILTER_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_index_spec",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"x": 1},
            "indexes": [{"x": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept a single index specification document",
    ),
    CommandTestCase(
        "compound_index_spec",
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
        "wildcard_index_spec",
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


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_INDEX_TESTS))
def test_planCacheSetFilter_index_filters(database_client, collection, test):
    """Test planCacheSetFilter index filter specification."""
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
