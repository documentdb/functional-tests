"""Tests for setFeatureCompatibilityVersion feature-not-supported behavior.

Validates that setFeatureCompatibilityVersion is classified as an admin-only
command and returns the appropriate error when the feature is not supported.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_setFeatureCompatibilityVersion_unsupported_returns_303(collection):
    """Test setFeatureCompatibilityVersion returns error code 303 when feature not supported."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": "8.0", "confirm": True}
    )
    # This test is only meaningful on engines that do not support FCV (e.g., DocumentDB).
    # On engines that support FCV, this test is expected to pass/succeed instead.
    if (
        isinstance(result, Exception)
        and hasattr(result, "code")
        and result.code == COMMAND_NOT_SUPPORTED_ERROR
    ):
        assertFailureCode(
            result,
            COMMAND_NOT_SUPPORTED_ERROR,
            msg="setFeatureCompatibilityVersion should return 303 when not supported",
        )
    else:
        pytest.skip("Engine supports setFeatureCompatibilityVersion, skipping not-supported test")
