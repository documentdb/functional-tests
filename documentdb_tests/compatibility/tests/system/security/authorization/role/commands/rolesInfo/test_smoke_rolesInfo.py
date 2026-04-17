"""
Smoke test for rolesInfo command.

Tests basic rolesInfo functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_rolesInfo(collection):
    """Test basic rolesInfo behavior."""
    result = execute_admin_command(collection, {"rolesInfo": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support rolesInfo command")
