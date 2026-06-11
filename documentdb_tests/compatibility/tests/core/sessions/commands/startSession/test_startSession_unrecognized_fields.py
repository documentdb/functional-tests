"""Tests for startSession unrecognized field handling."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Unrecognized Field Acceptance]: unknown fields are silently ignored.
STARTSESSION_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_single",
        command=lambda ctx: {"startSession": 1, "unknownField": 1},
        expected={"ok": Eq(1.0)},
        msg="startSession should silently ignore a single unknown field",
    ),
    CommandTestCase(
        "unrecognized_multiple",
        command=lambda ctx: {"startSession": 1, "foo": 1, "bar": 2},
        expected={"ok": Eq(1.0)},
        msg="startSession should silently ignore multiple unknown fields",
    ),
    CommandTestCase(
        "unrecognized_dollar_prefixed",
        command=lambda ctx: {"startSession": 1, "$unknown": 1},
        expected={"ok": Eq(1.0)},
        msg="startSession should silently ignore dollar-prefixed unknown fields",
    ),
    CommandTestCase(
        "unrecognized_known_from_other_command",
        command=lambda ctx: {"startSession": 1, "query": {"x": 1}},
        expected={"ok": Eq(1.0)},
        msg="startSession should silently ignore fields from other commands",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_UNRECOGNIZED_FIELD_TESTS))
def test_startSession_unrecognized_fields(database_client, collection, test):
    """Test startSession unrecognized field acceptance."""
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
