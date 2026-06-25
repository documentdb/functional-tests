"""Tests for planCacheClear command parameter independence and unknown fields."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Parameter Independence]: sort, projection, and collation succeed
# without query.
PLANCACHECLEAR_PARAM_INDEPENDENCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dep_sort_without_query",
        command=lambda ctx: {"planCacheClear": ctx.collection, "sort": {"a": 1}},
        expected={"ok": 1.0},
        msg="planCacheClear should accept sort without query",
    ),
    CommandTestCase(
        "dep_projection_without_query",
        command=lambda ctx: {"planCacheClear": ctx.collection, "projection": {"a": 1}},
        expected={"ok": 1.0},
        msg="planCacheClear should accept projection without query",
    ),
    CommandTestCase(
        "dep_sort_projection_without_query",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "sort": {"a": 1},
            "projection": {"a": 1},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept sort and projection without query",
    ),
    CommandTestCase(
        "dep_collation_without_query",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept collation without query",
    ),
]

# Property [Unknown Fields Accepted]: planCacheClear silently accepts
# unrecognized fields without error.
PLANCACHECLEAR_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field_foo",
        command=lambda ctx: {"planCacheClear": ctx.collection, "foo": 1},
        expected={"ok": 1.0},
        msg="planCacheClear should accept unknown field 'foo'",
    ),
    CommandTestCase(
        "unknown_field_uppercase_query",
        command=lambda ctx: {"planCacheClear": ctx.collection, "Query": {"a": 1}},
        expected={"ok": 1.0},
        msg="planCacheClear should accept 'Query' (case variation treated as unknown)",
    ),
    CommandTestCase(
        "unknown_field_uppercase_sort",
        command=lambda ctx: {"planCacheClear": ctx.collection, "Sort": {"a": 1}},
        expected={"ok": 1.0},
        msg="planCacheClear should accept 'Sort' (case variation treated as unknown)",
    ),
    CommandTestCase(
        "unknown_field_uppercase_projection",
        command=lambda ctx: {"planCacheClear": ctx.collection, "Projection": {"a": 1}},
        expected={"ok": 1.0},
        msg="planCacheClear should accept 'Projection' (case variation treated as unknown)",
    ),
]

PLANCACHECLEAR_DEPENDENCIES_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_PARAM_INDEPENDENCE_TESTS + PLANCACHECLEAR_UNKNOWN_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_DEPENDENCIES_TESTS))
def test_planCacheClear_dependencies(database_client, collection, test):
    """Test planCacheClear command parameter independence and unknown fields."""
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
