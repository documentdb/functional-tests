"""Tests for planCacheClearFilters command core behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
)

# Property [Basic Success]: planCacheClearFilters succeeds on existing, empty,
# and non-existent collections, returning ok: 1.0.
CLEAR_FILTERS_BASIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "basic_with_documents",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed on collection with documents",
    ),
    CommandTestCase(
        "basic_empty_collection",
        docs=[],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed on empty collection",
    ),
    CommandTestCase(
        "basic_nonexistent_collection",
        docs=None,
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed on non-existent collection",
    ),
]

# Property [Query Shape]: planCacheClearFilters accepts optional query, sort,
# and projection parameters to target a specific index filter.
CLEAR_FILTERS_QUERY_SHAPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_only",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept query only",
    ),
    CommandTestCase(
        "query_and_sort",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept query and sort",
    ),
    CommandTestCase(
        "query_and_projection",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept query and projection",
    ),
    CommandTestCase(
        "query_sort_projection",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept query, sort, and projection",
    ),
]

# Property [Parameter Combinations]: planCacheClearFilters supports various
# valid combinations of all parameters.
CLEAR_FILTERS_PARAM_COMBO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_sort_projection_comment",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept query, sort, projection, and comment",
    ),
    CommandTestCase(
        "query_sort_projection_collation",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept query, sort, projection, and collation",
    ),
    CommandTestCase(
        "all_parameters",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "sort": {"a": 1},
            "projection": {"a": 1},
            "collation": {"locale": "en"},
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept all parameters together",
    ),
    CommandTestCase(
        "comment_only",
        command=lambda ctx: {"planCacheClearFilters": ctx.collection, "comment": "test"},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept comment without query shape",
    ),
    CommandTestCase(
        "query_and_comment",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept query and comment",
    ),
]

# Property [Null Optional Parameters]: when optional parameters are set to
# null, the command treats them as omitted and succeeds.
CLEAR_FILTERS_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_query",
        command=lambda ctx: {"planCacheClearFilters": ctx.collection, "query": None},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat null query as omitted",
    ),
    CommandTestCase(
        "null_sort",
        command=lambda ctx: {"planCacheClearFilters": ctx.collection, "sort": None},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat null sort as omitted",
    ),
    CommandTestCase(
        "null_projection",
        command=lambda ctx: {"planCacheClearFilters": ctx.collection, "projection": None},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat null projection as omitted",
    ),
    CommandTestCase(
        "null_comment",
        command=lambda ctx: {"planCacheClearFilters": ctx.collection, "comment": None},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat null comment as omitted",
    ),
    CommandTestCase(
        "null_all_optional",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": None,
            "sort": None,
            "projection": None,
            "comment": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat all null optional params as omitted",
    ),
]

# Property [Parameter Independence]: sort, projection, and collation succeed
# without query.
CLEAR_FILTERS_INDEPENDENCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_without_query",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "sort": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept sort without query",
    ),
    CommandTestCase(
        "projection_without_query",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept projection without query",
    ),
    CommandTestCase(
        "sort_and_projection_without_query",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "sort": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept sort and projection without query",
    ),
    CommandTestCase(
        "collation_without_query",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept collation without query",
    ),
]

# Property [Capped Collection]: planCacheClearFilters succeeds on capped
# collections.
CLEAR_FILTERS_CAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed on a capped collection",
    ),
]

# Property [Clustered Collection]: planCacheClearFilters succeeds on clustered
# collections.
CLEAR_FILTERS_CLUSTERED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clustered_collection",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed on a clustered collection",
    ),
]

CLEAR_FILTERS_CORE_TESTS: list[CommandTestCase] = (
    CLEAR_FILTERS_BASIC_TESTS
    + CLEAR_FILTERS_QUERY_SHAPE_TESTS
    + CLEAR_FILTERS_PARAM_COMBO_TESTS
    + CLEAR_FILTERS_NULL_TESTS
    + CLEAR_FILTERS_INDEPENDENCE_TESTS
    + CLEAR_FILTERS_CAPPED_TESTS
    + CLEAR_FILTERS_CLUSTERED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CLEAR_FILTERS_CORE_TESTS))
def test_planCacheClearFilters_core(database_client, collection, test):
    """Test planCacheClearFilters command core behavior."""
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
