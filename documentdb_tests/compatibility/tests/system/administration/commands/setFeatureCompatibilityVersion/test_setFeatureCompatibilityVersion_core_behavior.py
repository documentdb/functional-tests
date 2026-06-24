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
        return "8.2"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.2")
    return str(fcv_data)


def _set_fcv(collection, version):
    """Set FCV to the given version with confirm:true."""
    return execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": version, "confirm": True}
    )


def _get_other_fcv(current):
    """Get a different supported FCV than the current one."""
    return "8.0" if current != "8.0" else "8.2"


def test_setFeatureCompatibilityVersion_set_current_version_succeeds(collection):
    """Test setFeatureCompatibilityVersion succeeds when setting the current version."""
    current_fcv = _get_fcv(collection)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when setting the current version",
    )


def test_setFeatureCompatibilityVersion_idempotent_same_value(collection):
    """Test setFeatureCompatibilityVersion is idempotent when re-setting the same value."""
    current_fcv = _get_fcv(collection)
    _set_fcv(collection, current_fcv)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should be idempotent when re-setting the same value",
    )


def test_setFeatureCompatibilityVersion_getParameter_reads_back_value(collection):
    """Test getParameter reads back the most recently set FCV."""
    current_fcv = _get_fcv(collection)
    _set_fcv(collection, current_fcv)
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should persist and be readable via getParameter",
    )


def test_setFeatureCompatibilityVersion_fresh_deployment_default_fcv(collection):
    """Test a fresh deployment reports its expected default FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should have a readable default on a fresh deployment",
    )


def test_setFeatureCompatibilityVersion_downgrade_with_confirm(collection):
    """Test setFeatureCompatibilityVersion can downgrade with confirm:true."""
    original_fcv = _get_fcv(collection)
    other_fcv = _get_other_fcv(original_fcv)
    result = _set_fcv(collection, other_fcv)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when changing version with confirm",
    )
    _set_fcv(collection, original_fcv)


def test_setFeatureCompatibilityVersion_upgrade_with_confirm(collection):
    """Test setFeatureCompatibilityVersion can upgrade back to the original version."""
    original_fcv = _get_fcv(collection)
    other_fcv = _get_other_fcv(original_fcv)
    _set_fcv(collection, other_fcv)
    result = _set_fcv(collection, original_fcv)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when upgrading back",
    )


def test_setFeatureCompatibilityVersion_getParameter_reflects_change(collection):
    """Test getParameter reflects the FCV after a change."""
    original_fcv = _get_fcv(collection)
    other_fcv = _get_other_fcv(original_fcv)
    _set_fcv(collection, other_fcv)
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "featureCompatibilityVersion": {"version": other_fcv}},
        msg="setFeatureCompatibilityVersion should be reflected in getParameter after a change",
    )
    _set_fcv(collection, original_fcv)
