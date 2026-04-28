"""
Smoke test for setFeatureCompatibilityVersion command.

Tests basic setFeatureCompatibilityVersion functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_setFeatureCompatibilityVersion(collection):
    """Test basic setFeatureCompatibilityVersion behavior."""
    get_result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )

    original_fcv = "8.2"
    if not isinstance(get_result, Exception):
        fcv_data = get_result.get("featureCompatibilityVersion", {})
        if isinstance(fcv_data, dict):
            original_fcv = fcv_data.get("version", "8.2")
        else:
            original_fcv = str(fcv_data)

    new_fcv = "8.2" if original_fcv != "8.2" else "8.0"
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": new_fcv, "confirm": True}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(
        result, expected, msg="Should support setFeatureCompatibilityVersion command"
    )

    execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": original_fcv, "confirm": True}
    )
