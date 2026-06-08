"""Tests for planCacheClearFilters command edge cases and permissiveness."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import NamedCollection

# Property [Unknown Fields Accepted]: planCacheClearFilters silently accepts
# unrecognized fields without error.
CLEAR_FILTERS_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field_foo",
        command=lambda ctx: {"planCacheClearFilters": ctx.collection, "foo": "bar"},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should silently accept unknown field",
    ),
    CommandTestCase(
        "case_variation_Query",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "Query": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat capitalized Query as unknown field",
    ),
    CommandTestCase(
        "case_variation_Sort",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "Sort": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat capitalized Sort as unknown field",
    ),
    CommandTestCase(
        "case_variation_Projection",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "Projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should treat capitalized Projection as unknown field",
    ),
]

# Property [Collation Valid]: planCacheClearFilters accepts valid collation
# with query.
CLEAR_FILTERS_COLLATION_VALID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_locale_en",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept collation with locale en",
    ),
    CommandTestCase(
        "collation_locale_fr_strength_2",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "query": {"a": 1},
            "collation": {"locale": "fr", "strength": 2},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept collation with locale and strength",
    ),
]

# Property [Collation Permissiveness]: collation accepts values that would
# normally be invalid because MongoDB silently accepts them in this command.
CLEAR_FILTERS_COLLATION_PERMISSIVE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_empty_document",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "collation": {},
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept empty collation document",
    ),
    CommandTestCase(
        "collation_string",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "collation": "en",
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept string collation",
    ),
    CommandTestCase(
        "collation_int",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "collation": 123,
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept int collation",
    ),
    CommandTestCase(
        "collation_bool",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "collation": True,
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept bool collation",
    ),
    CommandTestCase(
        "collation_array",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "collation": [1],
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept array collation",
    ),
    CommandTestCase(
        "collation_null",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "collation": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should accept null collation",
    ),
]

# Property [Collection Name Edge Cases]: planCacheClearFilters succeeds with
# special characters, unicode, and long collection names.
CLEAR_FILTERS_NAME_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_long",
        target_collection=NamedCollection(suffix="_" + "a" * 150),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed with a long collection name",
    ),
    CommandTestCase(
        "name_hyphen",
        target_collection=NamedCollection(suffix="_my-coll"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed with hyphen in name",
    ),
    CommandTestCase(
        "name_unicode",
        target_collection=NamedCollection(suffix="_\u00e9"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed with unicode name",
    ),
]

# Property [Comment Edge Cases]: planCacheClearFilters succeeds with edge-case
# comment values.
CLEAR_FILTERS_COMMENT_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_long",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "comment": "x" * 10_000,
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed with very long comment",
    ),
    CommandTestCase(
        "comment_empty_string",
        command=lambda ctx: {
            "planCacheClearFilters": ctx.collection,
            "comment": "",
        },
        expected={"ok": 1.0},
        msg="planCacheClearFilters should succeed with empty string comment",
    ),
]

CLEAR_FILTERS_EDGE_CASE_TESTS: list[CommandTestCase] = (
    CLEAR_FILTERS_UNKNOWN_FIELD_TESTS
    + CLEAR_FILTERS_COLLATION_VALID_TESTS
    + CLEAR_FILTERS_COLLATION_PERMISSIVE_TESTS
    + CLEAR_FILTERS_NAME_EDGE_CASE_TESTS
    + CLEAR_FILTERS_COMMENT_EDGE_CASE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CLEAR_FILTERS_EDGE_CASE_TESTS))
def test_planCacheClearFilters_edge_cases(database_client, collection, test):
    """Test planCacheClearFilters command edge cases and permissiveness."""
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
