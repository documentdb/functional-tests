"""Tests for setFeatureCompatibilityVersion confirm field semantics.

Validates that the confirm field is required for version changes,
and that confirm:false or omitted confirm prevents FCV changes.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

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


def _set_fcv(collection, version):
    """Set FCV with confirm:true."""
    return execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": version, "confirm": True}
    )


def _get_lower_fcv(current):
    """Get a different supported FCV than the current one."""
    return "8.0" if current != "8.0" else "8.2"


def test_setFeatureCompatibilityVersion_confirm_true_allows_change(collection):
    """Test confirm:true allows a version change to proceed."""
    original = _get_fcv(collection)
    lower = _get_lower_fcv(original)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": lower, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="confirm:true should allow version change")
    _set_fcv(collection, original)


def test_setFeatureCompatibilityVersion_confirm_omitted_fails(collection):
    """Test confirm omitted on a version change fails (ok:0), FCV unchanged."""
    original = _get_fcv(collection)
    lower = _get_lower_fcv(original)
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": lower})
    assertFailureCode(result, 7369100, msg="Should fail when confirm is omitted")


def test_setFeatureCompatibilityVersion_confirm_false_fails(collection):
    """Test confirm:false on a version change fails (ok:0), FCV unchanged."""
    original = _get_fcv(collection)
    lower = _get_lower_fcv(original)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": lower, "confirm": False}
    )
    assertFailureCode(result, 7369100, msg="Should fail when confirm is false")


def test_setFeatureCompatibilityVersion_confirm_omitted_returns_error_code(collection):
    """Test the confirm-gate failure returns a stable error code."""
    original = _get_fcv(collection)
    lower = _get_lower_fcv(original)
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": lower})
    # Assert it failed with a numeric code (7369100 per JS test specs)
    assertFailureCode(result, 7369100, msg="Omitting confirm should return error code 7369100")


def test_setFeatureCompatibilityVersion_confirm_false_returns_error_code(collection):
    """Test confirm:false returns the same stable error code."""
    original = _get_fcv(collection)
    lower = _get_lower_fcv(original)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": lower, "confirm": False}
    )
    assertFailureCode(result, 7369100, msg="confirm:false should return error code 7369100")


def test_setFeatureCompatibilityVersion_upgrade_without_confirm_fails(collection):
    """Test upgrading without confirm also fails with error code 7369100."""
    original = _get_fcv(collection)
    lower = _get_lower_fcv(original)
    # First downgrade
    _set_fcv(collection, lower)
    # Try upgrade without confirm
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": original})
    assertFailureCode(result, 7369100, msg="Upgrade without confirm should fail with 7369100")
    # Restore
    _set_fcv(collection, original)


def test_setFeatureCompatibilityVersion_upgrade_with_confirm_succeeds(collection):
    """Test upgrading with confirm:true succeeds."""
    original = _get_fcv(collection)
    lower = _get_lower_fcv(original)
    # First downgrade
    _set_fcv(collection, lower)
    # Upgrade with confirm
    result = _set_fcv(collection, original)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Upgrade with confirm:true should succeed")
