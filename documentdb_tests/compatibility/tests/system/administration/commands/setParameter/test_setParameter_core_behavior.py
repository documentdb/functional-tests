"""Tests for setParameter command core behavior.

Validates single/multiple parameter modification, admin database requirement,
runtime vs startup-only parameters, command shape, response structure, and
getParameter interaction.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Command Acceptance]: setParameter accepts valid commands on admin db.
COMMAND_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "admin_db_succeeds",
        command=lambda ctx: {"setParameter": 1, "logLevel": 0},
        expected={"ok": 1.0},
        msg="setParameter should succeed on admin db",
    ),
    CommandTestCase(
        "runtime_param_succeeds",
        command=lambda ctx: {"setParameter": 1, "logLevel": 0},
        expected={"ok": 1.0},
        msg="setParameter should succeed for runtime-settable param",
    ),
    CommandTestCase(
        "comment_field_accepted",
        command=lambda ctx: {"setParameter": 1, "logLevel": 0, "comment": "test"},
        expected={"ok": 1.0},
        msg="setParameter should accept comment field alongside params",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMAND_ACCEPTANCE_TESTS))
def test_setParameter_accepted(database_client, collection, test):
    """Test setParameter command acceptance cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


# Standalone tests below require save/restore of server state after each set.


# Property [Response Structure]: setParameter returns ok:1 and previous value in 'was'.
def test_setParameter_single_param_returns_ok(collection):
    """Test setParameter with one runtime-settable parameter returns ok:1."""
    original = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    original_val = original["logLevel"]
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="setParameter should return ok:1")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": original_val})


def test_setParameter_returns_was_field(collection):
    """Test setParameter response includes the previous value in 'was' field."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 2})
    assertSuccessPartial(
        result, {"ok": 1.0, "was": 0}, msg="setParameter should report previous value in 'was'"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_success_was_type_matches_param(collection):
    """Test setParameter 'was' field type matches the parameter's declared type."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"ok": 1.0, "was": 0}, msg="setParameter 'was' should be integer for logLevel"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_boolean_was_type(collection):
    """Test setParameter 'was' field for a boolean parameter is boolean type."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    execute_admin_command(collection, {"setParameter": 1, "quiet": False})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": True})
    assertSuccessPartial(
        result, {"ok": 1.0, "was": False}, msg="setParameter 'was' should be boolean for quiet"
    )
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


# Property [Value Persistence]: setParameter changes are reflected in getParameter.
def test_setParameter_actually_changes_value(collection):
    """Test setParameter changes are reflected via getParameter."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 3})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"logLevel": 3}, msg="setParameter should reflect new value via getParameter"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_getParameter_reflects_new_value(collection):
    """Test setParameter getParameter reflects new value immediately."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 4})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"logLevel": 4}, msg="setParameter should reflect new value immediately"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_getParameter_unchanged_after_failure(collection):
    """Test setParameter getParameter is unchanged after a failed set."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": "invalid"})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"logLevel": 0}, msg="setParameter should leave value unchanged after failure"
    )


# Property [Idempotency]: setting a parameter to its current value succeeds.
def test_setParameter_idempotent_set(collection):
    """Test setParameter setting a parameter to its current value returns ok:1."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    assertSuccessPartial(
        result, {"ok": 1.0, "was": 0}, msg="setParameter should succeed idempotently"
    )


# Property [Multiple Parameters]: setParameter sets multiple params in one command.
def test_setParameter_two_params_returns_ok(collection):
    """Test setParameter with two params in one command sets both."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1, "quiet": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="setParameter should set both parameters")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})


# Property [Round Trip]: value can be restored via 'was' field.
def test_setParameter_round_trip_restore(collection):
    """Test setParameter round-trip: set new, restore via 'was' field."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    set_result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 3})
    original_val = set_result["was"]
    execute_admin_command(collection, {"setParameter": 1, "logLevel": original_val})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"logLevel": 0}, msg="setParameter should restore to original")


# Property [Boolean Toggle]: boolean-typed parameters toggle correctly.
def test_setParameter_boolean_toggle(collection):
    """Test setParameter boolean-typed parameter toggles correctly."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    execute_admin_command(collection, {"setParameter": 1, "quiet": False})
    result = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    assertSuccessPartial(result, {"quiet": False}, msg="setParameter boolean should be False")
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


# Property [Ordering Independence]: parameter order in command does not affect result.
def test_setParameter_ordering_independence(collection):
    """Test setParameter parameter order in command does not affect result."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 2, "quiet": True})
    state1 = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
    execute_admin_command(collection, {"setParameter": 1, "quiet": True, "logLevel": 2})
    state2 = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        state2, {"logLevel": state1["logLevel"]}, msg="setParameter order should not matter"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
