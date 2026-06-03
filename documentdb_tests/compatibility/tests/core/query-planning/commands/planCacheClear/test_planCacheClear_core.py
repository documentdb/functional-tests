"""Tests for planCacheClear command core behavior.

Covers basic success cases, query shape variations, parameter combinations,
null/missing optional parameters, idempotency, and response structure.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
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
        "shape_query_only",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query only",
    ),
    CommandTestCase(
        "shape_query_sort",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query and sort",
    ),
    CommandTestCase(
        "shape_query_projection",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query and projection",
    ),
    CommandTestCase(
        "shape_query_sort_projection",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with query, sort, and projection",
    ),
    CommandTestCase(
        "shape_empty_query",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with an empty query document",
    ),
    CommandTestCase(
        "shape_empty_sort",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with an empty sort document",
    ),
    CommandTestCase(
        "shape_empty_projection",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "projection": {},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with an empty projection document",
    ),
]

# Property [Query Variations]: planCacheClear accepts various valid query
# structures including comparison operators, logical combinators, and nesting.
PLANCACHECLEAR_QUERY_VARIATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_equality",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with simple equality query",
    ),
    CommandTestCase(
        "query_comparison_gt",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": {"$gt": 10}},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with $gt comparison query",
    ),
    CommandTestCase(
        "query_multi_field",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1, "b": 2},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with multi-field query",
    ),
    CommandTestCase(
        "query_dotted_field",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a.b": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with dotted field name in query",
    ),
    CommandTestCase(
        "query_and_combinator",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"$and": [{"a": 1}, {"b": 2}]},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with $and combinator in query",
    ),
    CommandTestCase(
        "query_or_combinator",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"$or": [{"a": 1}, {"b": 2}]},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with $or combinator in query",
    ),
    CommandTestCase(
        "query_in_operator",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": {"$in": [1, 2, 3]}},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with $in operator in query",
    ),
    CommandTestCase(
        "query_deeply_nested",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": {"b": {"c": {"$gt": 1}}}},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with deeply nested query structure",
    ),
]

# Property [Sort Variations]: planCacheClear accepts ascending and descending
# sort directions as part of the query shape.
PLANCACHECLEAR_SORT_VARIATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_ascending",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with ascending sort",
    ),
    CommandTestCase(
        "sort_descending",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": -1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with descending sort",
    ),
]

# Property [Projection Variations]: planCacheClear accepts inclusion and
# exclusion projections as part of the query shape.
PLANCACHECLEAR_PROJECTION_VARIATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "projection_inclusion",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with inclusion projection",
    ),
    CommandTestCase(
        "projection_exclusion_and_inclusion",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "projection": {"_id": 0, "a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should succeed with _id exclusion and field inclusion projection",
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

# Property [Idempotency]: calling planCacheClear multiple times on the same
# collection succeeds each time.
PLANCACHECLEAR_IDEMPOTENCY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "idempotent_no_cached_plans",
        command=lambda ctx: {"planCacheClear": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClear should succeed as a no-op on a collection with no cached plans",
    ),
]

PLANCACHECLEAR_CORE_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_BASIC_SUCCESS_TESTS
    + PLANCACHECLEAR_QUERY_SHAPE_TESTS
    + PLANCACHECLEAR_QUERY_VARIATION_TESTS
    + PLANCACHECLEAR_SORT_VARIATION_TESTS
    + PLANCACHECLEAR_PROJECTION_VARIATION_TESTS
    + PLANCACHECLEAR_PARAM_COMBO_TESTS
    + PLANCACHECLEAR_NULL_PARAMS_TESTS
    + PLANCACHECLEAR_IDEMPOTENCY_TESTS
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
