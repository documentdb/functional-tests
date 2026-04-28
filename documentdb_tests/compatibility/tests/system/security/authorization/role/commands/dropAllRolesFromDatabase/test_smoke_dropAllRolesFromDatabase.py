"""
Smoke test for dropAllRolesFromDatabase command.

Tests basic dropAllRolesFromDatabase functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_dropAllRolesFromDatabase(collection):
    """Test basic dropAllRolesFromDatabase behavior."""
    result = execute_admin_command(collection, {"dropAllRolesFromDatabase": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support dropAllRolesFromDatabase command")
