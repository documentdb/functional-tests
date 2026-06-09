"""Tests for planCacheSetFilter query field and sort field edge cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


# Property [Query Edge Cases]: planCacheSetFilter accepts various query predicates.
QUERY_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_query_document",
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
        "nested_query_predicate",
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
        "query_with_operators",
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
        "query_with_multiple_fields",
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
        "complex_query_predicate",
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

# Property [Sort Edge Cases]: planCacheSetFilter accepts various sort specifications.
SORT_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_with_multiple_fields",
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

SET_FILTER_EDGE_CASE_TESTS: list[CommandTestCase] = (
    QUERY_EDGE_CASE_TESTS + SORT_EDGE_CASE_TESTS
)


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_EDGE_CASE_TESTS))
def test_planCacheSetFilter_edge_cases(database_client, collection, test):
    """Test planCacheSetFilter query and sort edge cases."""
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
