"""Shared fixtures for setFeatureCompatibilityVersion tests.

Provides an autouse fixture that snapshots the FCV before each test and
unconditionally restores it after, preventing leaked state even when a test
fails.
"""

import pytest

from documentdb_tests.framework.executor import execute_admin_command


@pytest.fixture(autouse=True)
def restore_fcv(collection):
    """Snapshot FCV before the test, restore after.

    This runs unconditionally (autouse) so that any test modifying FCV
    cannot leak changes into subsequent tests — whether it passes, fails, or errors.
    """
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, dict):
        fcv_data = result.get("featureCompatibilityVersion", {})
        original_fcv = fcv_data.get("version", "8.2") if isinstance(fcv_data, dict) else "8.2"
    else:
        original_fcv = "8.2"

    yield

    execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": original_fcv, "confirm": True}
    )
