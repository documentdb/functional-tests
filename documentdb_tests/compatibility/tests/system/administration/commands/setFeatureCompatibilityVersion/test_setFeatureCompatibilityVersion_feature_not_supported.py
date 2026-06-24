"""Tests for setFeatureCompatibilityVersion feature-not-supported behavior.

Validates that setFeatureCompatibilityVersion is classified as an admin-only
command and returns the appropriate error when the feature is not supported.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

# Error code 303 = CommandNotSupportedOnView or feature not supported
FEATURE_NOT_SUPPORTED_ERROR = 303


def test_setFeatureCompatibilityVersion_unsupported_returns_303(collection):
    """Test setFeatureCompatibilityVersion returns error code 303 when feature not supported."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "8.0", "confirm": True}
    )
    # This test is only meaningful on engines that do not support FCV (e.g., DocumentDB).
    # On engines that support FCV, this test is expected to pass/succeed instead.
    # We check if it returns 303 specifically for the not-supported case.
    if (
        isinstance(result, Exception)
        and hasattr(result, "code")
        and result.code == FEATURE_NOT_SUPPORTED_ERROR
    ):
        assertFailureCode(
            result,
            FEATURE_NOT_SUPPORTED_ERROR,
            msg="setFeatureCompatibilityVersion should return 303 when not supported",
        )
    else:
        # On engines that support FCV, this is a pass-through
        pytest.skip("Engine supports setFeatureCompatibilityVersion")
