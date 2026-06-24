"""Tests for setFeatureCompatibilityVersion version value validation.

Validates that the version field rejects unsupported, malformed, and
edge-case string values with FCV_INVALID_VERSION_ERROR (2).
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

# MongoDB 8.2 uses this error code for invalid FCV version values
FCV_INVALID_VERSION_ERROR = 4926900


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


def test_setFeatureCompatibilityVersion_value_below_floor_rejected(collection):
    """Test a value below the binary's supported floor is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "3.0", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Version below supported floor should be rejected"
    )


def test_setFeatureCompatibilityVersion_value_above_max_rejected(collection):
    """Test a value above the binary's max supported FCV is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "99.0", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Version above max supported should be rejected"
    )


def test_setFeatureCompatibilityVersion_major_only_rejected(collection):
    """Test a malformed value with no minor ('8') is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "8", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Major-only version string should be rejected"
    )


def test_setFeatureCompatibilityVersion_full_semver_rejected(collection):
    """Test a full-semver value ('8.0.0') is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "8.0.0", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Full semver version string should be rejected"
    )


def test_setFeatureCompatibilityVersion_leading_whitespace_rejected(collection):
    """Test a value with leading whitespace (' 7.0') is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": " 7.0", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Version with leading whitespace should be rejected"
    )


def test_setFeatureCompatibilityVersion_trailing_whitespace_rejected(collection):
    """Test a value with trailing whitespace ('7.0 ') is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "7.0 ", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Version with trailing whitespace should be rejected"
    )


def test_setFeatureCompatibilityVersion_empty_string_rejected(collection):
    """Test an empty-string value is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Empty string version should be rejected"
    )


def test_setFeatureCompatibilityVersion_zero_version_rejected(collection):
    """Test '0.0' is rejected as an unsupported version."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "0.0", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="'0.0' should be rejected as unsupported"
    )


def test_setFeatureCompatibilityVersion_future_version_rejected(collection):
    """Test '10.0' is rejected as a future unsupported version."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "10.0", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="'10.0' should be rejected as unsupported"
    )


def test_setFeatureCompatibilityVersion_non_ascii_rejected(collection):
    """Test a non-ASCII/unicode-digit value is rejected."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "８.０", "confirm": True}
    )
    assertFailureCode(result, FCV_INVALID_VERSION_ERROR, msg="Non-ASCII version should be rejected")


def test_setFeatureCompatibilityVersion_very_long_string_rejected(collection):
    """Test a very long string value is rejected without crash."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "8" * 10000, "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Very long version string should be rejected"
    )


def test_setFeatureCompatibilityVersion_intermediate_value_rejected(collection):
    """Test setting to an intermediate value between supported versions fails."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "7.5", "confirm": True}
    )
    assertFailureCode(
        result, FCV_INVALID_VERSION_ERROR, msg="Intermediate version '7.5' should be rejected"
    )


def test_setFeatureCompatibilityVersion_current_version_accepted(collection):
    """Test the current binary version is accepted as a valid value."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Current version should be accepted")
