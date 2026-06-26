"""Tests for setParameter command core behavior.

Validates single/multiple parameter modification, admin database requirement,
runtime vs startup-only parameters, command shape, response structure, and
getParameter interaction.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# --- Single Parameter Modification ---


def test_setParameter_single_param_returns_ok(collection):
    """Test setParameter with one runtime-settable parameter returns ok:1."""
    original = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    original_val = original["logLevel"]
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should return ok:1")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": original_val})


def test_setParameter_returns_was_field(collection):
    """Test setParameter response includes the previous value in 'was' field."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 2})
    assertSuccessPartial(result, {"ok": 1.0, "was": 0}, msg="Should report previous value in 'was'")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_actually_changes_value(collection):
    """Test setParameter actually changes the parameter value verified via getParameter."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 3})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"logLevel": 3}, msg="Should reflect new value via getParameter")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_idempotent_set(collection):
    """Test setting a parameter to its current value returns ok:1 with was equal to new value."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    assertSuccessPartial(result, {"ok": 1.0, "was": 0}, msg="Idempotent set should succeed")


# --- Multiple Parameter Modification ---


def test_setParameter_two_params_returns_ok(collection):
    """Test setParameter with two runtime-settable parameters in one command sets both."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1, "quiet": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should set both parameters")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})


# --- Admin Database Requirement ---


def test_setParameter_on_admin_db_succeeds(collection):
    """Test setParameter run against the admin database succeeds."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed on admin db")


def test_setParameter_on_non_admin_db_fails(collection):
    """Test setParameter run against a non-admin database fails with Unauthorized error."""
    result = execute_command(collection, {"setParameter": 1, "logLevel": 0})
    assertFailureCode(result, UNAUTHORIZED_ERROR, msg="Should fail on non-admin db")


# --- Runtime vs Startup-Only Parameters ---


def test_setParameter_runtime_param_succeeds(collection):
    """Test setParameter on a runtime-settable parameter succeeds."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Runtime param should succeed")


def test_setParameter_startup_only_param_fails(collection):
    """Test setParameter on a startup-only parameter fails with InvalidOptions error."""
    result = execute_admin_command(collection, {"setParameter": 1, "port": 27018})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Startup-only param should fail")


def test_setParameter_nonexistent_param_fails(collection):
    """Test setParameter on a non-existent parameter name fails with InvalidOptions error."""
    result = execute_admin_command(collection, {"setParameter": 1, "nonExistentParam123": 1})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Non-existent param should fail")


# --- Command Shape ---


def test_setParameter_no_param_pair_fails(collection):
    """Test setParameter with control field but no parameter:value pair fails."""
    result = execute_admin_command(collection, {"setParameter": 1})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="No param pair should fail")


def test_setParameter_comment_field_accepted(collection):
    """Test comment field accepted alongside setParameter."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "logLevel": 0, "comment": "test comment"}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Comment field should be accepted")


# --- Response Structure ---


def test_setParameter_success_was_type_matches_param(collection):
    """Test the 'was' field type matches the parameter's declared type (integer for logLevel)."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"ok": 1.0, "was": 0}, msg="'was' should be integer type matching logLevel"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_boolean_was_type(collection):
    """Test the 'was' field for a boolean parameter is boolean type."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    execute_admin_command(collection, {"setParameter": 1, "quiet": False})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": True})
    assertSuccessPartial(result, {"ok": 1.0, "was": False}, msg="'was' should be boolean type")
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


# --- Interaction with getParameter ---


def test_setParameter_getParameter_reflects_new_value(collection):
    """Test getParameter reflects new value immediately after successful setParameter."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 4})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"logLevel": 4}, msg="getParameter should reflect new value")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_getParameter_unchanged_after_failure(collection):
    """Test getParameter is unchanged after a failed setParameter."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": "invalid"})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"logLevel": 0}, msg="Value should be unchanged after failure")


def test_setParameter_round_trip_restore(collection):
    """Test round-trip: read, set new, restore original via 'was' field."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    set_result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 3})
    original_val = set_result["was"]
    execute_admin_command(collection, {"setParameter": 1, "logLevel": original_val})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"logLevel": 0}, msg="Should restore to original")


# --- Boolean parameter toggle ---


def test_setParameter_boolean_toggle(collection):
    """Test setting a boolean-typed parameter to false and reading back."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    execute_admin_command(collection, {"setParameter": 1, "quiet": False})
    result = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    assertSuccessPartial(result, {"quiet": False}, msg="Boolean param should be False")
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


def test_setParameter_ordering_independence(collection):
    """Test setting {logLevel, quiet} vs {quiet, logLevel} yields same final state."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 2, "quiet": True})
    state1 = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
    execute_admin_command(collection, {"setParameter": 1, "quiet": True, "logLevel": 2})
    state2 = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(state2, {"logLevel": state1["logLevel"]}, msg="Order should not matter")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0, "quiet": False})
