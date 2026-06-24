"""
Smoke test for setFeatureCompatibilityVersion command.

Tests basic setFeatureCompatibilityVersion functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


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


def test_smoke_setFeatureCompatibilityVersion(collection):
    """Test basic setFeatureCompatibilityVersion behavior."""
    original_fcv = _get_fcv(collection)
    new_fcv = "8.0" if original_fcv != "8.0" else "8.2"
    result = _set_fcv(collection, new_fcv)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed with a valid version change",
    )
    _set_fcv(collection, original_fcv)
