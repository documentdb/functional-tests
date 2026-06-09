"""Tests for planCacheListFilters command edge cases and permissiveness."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import NamedCollection

# Property [Unknown Fields Accepted]: planCacheListFilters silently accepts
# unrecognized fields without error.
LIST_FILTERS_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field_foo",
        command=lambda ctx: {"planCacheListFilters": ctx.collection, "foo": "bar"},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should silently accept unknown field",
    ),
    CommandTestCase(
        "case_variation_Comment",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "Comment": "test",
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should treat capitalized Comment as unknown field",
    ),
    CommandTestCase(
        "case_variation_Query",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "Query": {"a": 1},
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should treat capitalized Query as unknown field",
    ),
    CommandTestCase(
        "case_variation_Sort",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "Sort": {"a": 1},
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should treat capitalized Sort as unknown field",
    ),
]

# Property [Collection Name Edge Cases]: planCacheListFilters succeeds with
# special characters, unicode, and long collection names.
LIST_FILTERS_NAME_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_long",
        target_collection=NamedCollection(suffix="_" + "a" * 150),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with a long collection name",
    ),
    CommandTestCase(
        "name_hyphen",
        target_collection=NamedCollection(suffix="_my-coll"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with hyphen in name",
    ),
    CommandTestCase(
        "name_unicode",
        target_collection=NamedCollection(suffix="_\u00e9"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with unicode name",
    ),
    CommandTestCase(
        "name_single_char",
        target_collection=NamedCollection(suffix="_x"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with single-character suffix name",
    ),
    CommandTestCase(
        "name_underscores",
        target_collection=NamedCollection(suffix="_my_test_coll"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with underscores in name",
    ),
]

# Property [Comment Edge Cases]: planCacheListFilters succeeds with edge-case
# comment values.
LIST_FILTERS_COMMENT_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_long",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": "x" * 10_000,
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with very long comment",
    ),
    CommandTestCase(
        "comment_empty_string",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": "",
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with empty string comment",
    ),
    CommandTestCase(
        "comment_deeply_nested",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": {"a": {"b": {"c": {"d": {"e": 1}}}}},
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with deeply nested object comment",
    ),
    CommandTestCase(
        "comment_mixed_array",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": [1, "two", True, None, {"a": 1}],
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with array of mixed types as comment",
    ),
]

LIST_FILTERS_EDGE_CASE_TESTS: list[CommandTestCase] = (
    LIST_FILTERS_UNKNOWN_FIELD_TESTS
    + LIST_FILTERS_NAME_EDGE_CASE_TESTS
    + LIST_FILTERS_COMMENT_EDGE_CASE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(LIST_FILTERS_EDGE_CASE_TESTS))
def test_planCacheListFilters_edge_cases(database_client, collection, test):
    """Test planCacheListFilters command edge cases and permissiveness."""
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
