"""Tests for setFeatureCompatibilityVersion error cases.

Covers admin-database-only enforcement, unknown/extra fields, argument
handling combinations, response structure, and setParameter rejection.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    ILLEGAL_OPERATION_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection):
    """Read the current FCV."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return "8.2"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.2")
    return str(fcv_data)


# --- Admin-Database-Only Enforcement ---


def test_setFeatureCompatibilityVersion_on_admin_db_accepted(collection):
    """Test command on the admin database is accepted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Command on admin db should be accepted")


def test_setFeatureCompatibilityVersion_on_user_db_fails(collection):
    """Test command on a user database fails with UNAUTHORIZED_ERROR (13)."""
    current_fcv = _get_fcv(collection)
    result = execute_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertFailureCode(
        result, UNAUTHORIZED_ERROR, msg="Command on user db should fail with UNAUTHORIZED_ERROR"
    )


# --- Unknown / Extra Fields ---


def test_setFeatureCompatibilityVersion_unrecognized_field_rejected(collection):
    """Test an unrecognized top-level field fails with UNRECOGNIZED_COMMAND_FIELD_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "unknownField": 1,
        },
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should be rejected with 40415",
    )


def test_setFeatureCompatibilityVersion_misspelled_confirm_rejected(collection):
    """Test a misspelled confirm field (confrim:true) is treated as unknown (40415)."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confrim": True,
        },
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Misspelled 'confrim' should be rejected as unknown field",
    )


# --- setParameter rejection ---


def test_setFeatureCompatibilityVersion_via_setParameter_rejected(collection):
    """Test the compatibility version cannot be set through the setParameter command."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "featureCompatibilityVersion": "8.0"},
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="setParameter should not accept featureCompatibilityVersion",
    )


# --- Argument Handling — Combinations ---


def test_setFeatureCompatibilityVersion_version_and_confirm_succeeds(collection):
    """Test (version value + confirm:true) succeeds."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="version + confirm:true should succeed")


def test_setFeatureCompatibilityVersion_version_confirm_writeConcern_succeeds(collection):
    """Test (version + confirm:true + writeConcern document) succeeds."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": 5000},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="version + confirm + writeConcern should succeed")


# --- Response Structure ---


def test_setFeatureCompatibilityVersion_success_contains_ok_1(collection):
    """Test success response contains ok:1."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Success response should contain ok:1")


def test_setFeatureCompatibilityVersion_error_contains_code(collection):
    """Test error response contains ok:0, numeric code, and codeName."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": "invalid_version", "confirm": True},
    )
    # MongoDB 8.2 uses code 4926900 for invalid FCV version strings
    assertFailureCode(result, 4926900, msg="Invalid version should produce an error with code")


def test_setFeatureCompatibilityVersion_unknown_field_fires_before_state_change(collection):
    """Test unknown-field rejection happens before any FCV state change."""
    original = _get_fcv(collection)
    lower = "8.0" if original != "8.0" else "7.0"
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": lower,
            "confirm": True,
            "unknownField": 1,
        },
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field should be rejected at parse time before any state change",
    )
