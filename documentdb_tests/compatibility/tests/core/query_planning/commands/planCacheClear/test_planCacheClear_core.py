"""Tests for planCacheClear command core behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Success]: planCacheClear succeeds on existing, empty, and
# non-existent collections, returning ok: 1.0.
PLANCACHECLEAR_BASIC_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "basic_with_docs",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {"planCacheClear": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClear should succeed on a collection with documents",
    ),
    CommandTestCase(
        "basic_empty_collection",
        docs=[],
        command=lambda ctx: {"planCacheClear": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClear should succeed on an explicitly created empty collection",
    ),
    CommandTestCase(
        "basic_nonexistent_collection",
        command=lambda ctx: {"planCacheClear": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClear should succeed silently on a non-existent collection",
    ),
]

# Property [Query Shape]: planCacheClear accepts optional query, sort, and
# projection parameters to target a specific cached query shape.
PLANCACHECLEAR_QUERY_SHAPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_only",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query only",
    ),
    CommandTestCase(
        "query_and_sort",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query and sort",
    ),
    CommandTestCase(
        "query_and_projection",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query and projection",
    ),
    CommandTestCase(
        "query_sort_and_projection",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query, sort, and projection",
    ),
]

# Property [Parameter Combinations]: planCacheClear supports various valid
# combinations of all parameters used together.
PLANCACHECLEAR_PARAM_COMBO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "combo_query_sort_projection_comment",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query, sort, projection, and comment combined",
    ),
    CommandTestCase(
        "combo_query_sort_projection_collation",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query, sort, projection, and collation combined",
    ),
    CommandTestCase(
        "combo_all_params",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
            "collation": {"locale": "en"},
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with all parameters combined",
    ),
    CommandTestCase(
        "combo_comment_only",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with only comment (no query shape)",
    ),
    CommandTestCase(
        "combo_query_comment",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query and comment",
    ),
]

# Property [Null Optional Parameters]: when optional parameters are set to
# null, the command treats them as omitted and succeeds.
PLANCACHECLEAR_NULL_PARAMS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_query",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed when query is null (treated as omitted)",
    ),
    CommandTestCase(
        "null_sort",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "sort": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed when sort is null (treated as omitted)",
    ),
    CommandTestCase(
        "null_projection",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "projection": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed when projection is null (treated as omitted)",
    ),
    CommandTestCase(
        "null_comment",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "comment": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed when comment is null",
    ),
    CommandTestCase(
        "null_all_optional",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": None,
            "sort": None,
            "projection": None,
            "comment": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed when all optional params are null",
    ),
]

PLANCACHECLEAR_CORE_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_BASIC_SUCCESS_TESTS
    + PLANCACHECLEAR_QUERY_SHAPE_TESTS
    + PLANCACHECLEAR_PARAM_COMBO_TESTS
    + PLANCACHECLEAR_NULL_PARAMS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_CORE_TESTS))
def test_planCacheClear_core(database_client, collection, test):
    """Test planCacheClear command core behavior."""
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
