"""Tests for setFeatureCompatibilityVersion version value validation.

Validates that the version field rejects unsupported, malformed, and
edge-case string values.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import FCV_INVALID_VERSION_ERROR
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


def test_setFeatureCompatibilityVersion_value_below_floor_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a version below the supported floor."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "3.0", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version below supported floor",
    )


def test_setFeatureCompatibilityVersion_value_above_max_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a version above the supported max."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "99.0", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version above supported max",
    )


def test_setFeatureCompatibilityVersion_major_only_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a major-only version string."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "8", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject major-only version string",
    )


def test_setFeatureCompatibilityVersion_full_semver_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a full semver string."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "8.0.0", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject full semver version string",
    )


def test_setFeatureCompatibilityVersion_leading_whitespace_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a version with leading whitespace."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": " 7.0", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version with leading whitespace",
    )


def test_setFeatureCompatibilityVersion_trailing_whitespace_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a version with trailing whitespace."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "7.0 ", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version with trailing whitespace",
    )


def test_setFeatureCompatibilityVersion_empty_string_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects an empty string."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject empty string version",
    )


def test_setFeatureCompatibilityVersion_zero_version_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects '0.0' as unsupported."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "0.0", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject '0.0' as unsupported",
    )


def test_setFeatureCompatibilityVersion_future_version_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a future unsupported version."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "10.0", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject future unsupported version",
    )


def test_setFeatureCompatibilityVersion_non_ascii_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects non-ASCII digit characters."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": "\uff18.\uff10", "confirm": True},
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject non-ASCII version string",
    )


def test_setFeatureCompatibilityVersion_very_long_string_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects a very long string."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": "8" * 10_000, "confirm": True},
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject a very long version string",
    )


def test_setFeatureCompatibilityVersion_intermediate_value_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects an intermediate version value."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "7.5", "confirm": True}
    )
    assertFailureCode(
        result,
        FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject intermediate version value",
    )


def test_setFeatureCompatibilityVersion_current_version_accepted(collection):
    """Test setFeatureCompatibilityVersion accepts the current binary version."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": True},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept the current binary version",
    )
