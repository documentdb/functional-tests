"""
Smoke test for getClusterParameter command.

Tests basic getClusterParameter functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_getClusterParameter(collection):
    """Test basic getClusterParameter behavior."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support getClusterParameter command")
