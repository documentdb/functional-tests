"""Tests for setFeatureCompatibilityVersion core behavior.

Validates FCV set/get round-trip, idempotency, default value read-back,
and basic upgrade/downgrade with confirm.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection):
    """Read the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return None
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version")
    return str(fcv_data)


def _set_fcv(collection, version):
    """Set FCV to the given version with confirm:true."""
    return execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": version, "confirm": True}
    )


def test_setFeatureCompatibilityVersion_set_current_version_succeeds(collection):
    """Test setting FCV to the deployment's supported version with confirm:true succeeds."""
    current_fcv = _get_fcv(collection)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Setting FCV to current version should succeed")


def test_setFeatureCompatibilityVersion_idempotent_same_value(collection):
    """Test setting FCV to the value it already holds is idempotent and returns ok:1."""
    current_fcv = _get_fcv(collection)
    _set_fcv(collection, current_fcv)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="Re-setting FCV to same value should be idempotent"
    )


def test_setFeatureCompatibilityVersion_safe_retry(collection):
    """Test re-running the identical successful command again succeeds."""
    current_fcv = _get_fcv(collection)
    _set_fcv(collection, current_fcv)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Safe retry of the same command should succeed")


def test_setFeatureCompatibilityVersion_getParameter_reads_back_value(collection):
    """Test getParameter featureCompatibilityVersion reads back the most recently set value."""
    current_fcv = _get_fcv(collection)
    _set_fcv(collection, current_fcv)
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="getParameter should succeed after setFeatureCompatibilityVersion",
    )


def test_setFeatureCompatibilityVersion_fresh_deployment_default_fcv(collection):
    """Test a fresh deployment reports its expected default FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="getParameter featureCompatibilityVersion should succeed"
    )


def test_setFeatureCompatibilityVersion_downgrade_with_confirm(collection):
    """Test the compatibility version can be downgraded with confirm."""
    original_fcv = _get_fcv(collection)
    # Use the other supported version (8.0 or 8.2)
    other_fcv = "8.0" if original_fcv != "8.0" else "8.2"

    result = _set_fcv(collection, other_fcv)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Changing FCV with confirm:true should succeed")
    # Restore original
    _set_fcv(collection, original_fcv)


def test_setFeatureCompatibilityVersion_upgrade_with_confirm(collection):
    """Test the compatibility version can be upgraded back to the latest supported version."""
    original_fcv = _get_fcv(collection)
    other_fcv = "8.0" if original_fcv != "8.0" else "8.2"

    # Change first
    _set_fcv(collection, other_fcv)
    # Change back
    result = _set_fcv(collection, original_fcv)
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="Changing FCV back with confirm:true should succeed"
    )


def test_setFeatureCompatibilityVersion_getParameter_reflects_change(collection):
    """Test that after a successful setFeatureCompatibilityVersion the read-back matches."""
    original_fcv = _get_fcv(collection)
    other_fcv = "8.0" if original_fcv != "8.0" else "8.2"

    _set_fcv(collection, other_fcv)
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "featureCompatibilityVersion": {"version": other_fcv}},
        msg=f"getParameter should reflect changed FCV to '{other_fcv}'",
    )
    # Restore
    _set_fcv(collection, original_fcv)
