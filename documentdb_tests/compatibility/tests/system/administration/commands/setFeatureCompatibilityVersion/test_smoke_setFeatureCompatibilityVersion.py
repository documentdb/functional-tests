"""
Smoke test for setFeatureCompatibilityVersion command.

Tests basic setFeatureCompatibilityVersion functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_setFeatureCompatibilityVersion(collection):
    """Test basic setFeatureCompatibilityVersion behavior."""
    original_fcv = get_fcv(collection)
    new_fcv = "8.0" if original_fcv != "8.0" else "8.2"
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": new_fcv, "confirm": True}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed with a valid version change",
    )
    execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": original_fcv, "confirm": True}
    )
