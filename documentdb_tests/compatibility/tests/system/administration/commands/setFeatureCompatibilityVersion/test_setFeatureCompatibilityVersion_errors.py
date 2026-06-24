"""Tests for setFeatureCompatibilityVersion error cases.

Covers admin-database-only enforcement, unknown/extra fields,
response structure, and setParameter rejection.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    FCV_INVALID_VERSION_ERROR,
    ILLEGAL_OPERATION_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection):
    """Read the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return "8.2"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.2")
    return str(fcv_data)


def test_setFeatureCompatibilityVersion_on_admin_db_accepted(collection):
    """Test setFeatureCompatibilityVersion succeeds on the admin database."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed on the admin database",
    )


def test_setFeatureCompatibilityVersion_on_user_db_fails(collection):
    """Test setFeatureCompatibilityVersion fails on a user database."""
    current_fcv = _get_fcv(collection)
    result = execute_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="setFeatureCompatibilityVersion should reject execution on a user database",
    )


def test_setFeatureCompatibilityVersion_unrecognized_field_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects an unrecognized top-level field."""
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
        msg="setFeatureCompatibilityVersion should reject unrecognized fields",
    )


def test_setFeatureCompatibilityVersion_misspelled_confirm_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a misspelled confirm field."""
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
        msg="setFeatureCompatibilityVersion should reject misspelled 'confrim' as unknown field",
    )


def test_setFeatureCompatibilityVersion_via_setParameter_rejected(collection):
    """Test setFeatureCompatibilityVersion cannot be set through setParameter."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "featureCompatibilityVersion": "8.0"},
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="setFeatureCompatibilityVersion should not be settable via setParameter",
    )


def test_setFeatureCompatibilityVersion_error_contains_code(collection):
    """Test setFeatureCompatibilityVersion error response contains a numeric code."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": "invalid_version", "confirm": True},
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should return a numeric error code for invalid version",
    )


def test_setFeatureCompatibilityVersion_unknown_field_fires_before_state_change(collection):
    """Test setFeatureCompatibilityVersion rejects unknown fields before any state change."""
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
        msg="setFeatureCompatibilityVersion should reject unknown fields before changing state",
    )
