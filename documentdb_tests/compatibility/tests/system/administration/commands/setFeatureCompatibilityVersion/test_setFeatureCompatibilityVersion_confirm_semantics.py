"""Tests for setFeatureCompatibilityVersion confirm field semantics.

Validates that the confirm field is required for version changes,
and that confirm:false or omitted confirm prevents FCV changes.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import FCV_CONFIRM_REQUIRED_ERROR
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


def _get_other_fcv(current):
    """Get a different supported FCV than the current one."""
    return "8.0" if current != "8.0" else "8.2"


def test_setFeatureCompatibilityVersion_confirm_true_allows_change(collection):
    """Test setFeatureCompatibilityVersion succeeds with confirm:true."""
    original = _get_fcv(collection)
    lower = _get_other_fcv(original)
    result = _set_fcv(collection, lower)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should allow version change with confirm:true",
    )
    _set_fcv(collection, original)


def test_setFeatureCompatibilityVersion_confirm_omitted_fails(collection):
    """Test setFeatureCompatibilityVersion fails when confirm is omitted."""
    original = _get_fcv(collection)
    lower = _get_other_fcv(original)
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": lower})
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject version change without confirm",
    )


def test_setFeatureCompatibilityVersion_confirm_false_fails(collection):
    """Test setFeatureCompatibilityVersion fails with confirm:false."""
    original = _get_fcv(collection)
    lower = _get_other_fcv(original)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": lower, "confirm": False}
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject version change with confirm:false",
    )


def test_setFeatureCompatibilityVersion_upgrade_without_confirm_fails(collection):
    """Test setFeatureCompatibilityVersion rejects upgrade without confirm."""
    original = _get_fcv(collection)
    lower = _get_other_fcv(original)
    _set_fcv(collection, lower)
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": original})
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject upgrade without confirm",
    )
    _set_fcv(collection, original)


def test_setFeatureCompatibilityVersion_upgrade_with_confirm_succeeds(collection):
    """Test setFeatureCompatibilityVersion succeeds on upgrade with confirm:true."""
    original = _get_fcv(collection)
    lower = _get_other_fcv(original)
    _set_fcv(collection, lower)
    result = _set_fcv(collection, original)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed on upgrade with confirm:true",
    )
