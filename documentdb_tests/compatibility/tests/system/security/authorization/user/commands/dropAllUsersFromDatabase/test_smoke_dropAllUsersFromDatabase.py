"""
Smoke test for dropAllUsersFromDatabase command.

Tests basic dropAllUsersFromDatabase functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_dropAllUsersFromDatabase(collection):
    """Test basic dropAllUsersFromDatabase behavior."""
    result = execute_admin_command(collection, {"dropAllUsersFromDatabase": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support dropAllUsersFromDatabase command")
