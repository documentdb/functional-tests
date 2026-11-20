"""
Smoke test for setFeatureCompatibilityVersion command.

Tests basic setFeatureCompatibilityVersion functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_setFeatureCompatibilityVersion(collection):
    """Test the engine accepts setFeatureCompatibilityVersion set to its own current version."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if not isinstance(result, Exception):
        current_fcv = result["featureCompatibilityVersion"]["version"]
        result = execute_admin_command(
            collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
        )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept the server's current version",
    )
