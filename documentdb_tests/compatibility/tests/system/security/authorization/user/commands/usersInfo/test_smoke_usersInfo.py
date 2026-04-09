"""
Smoke test for usersInfo command.

Tests basic usersInfo functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_usersInfo(collection):
    """Test basic usersInfo behavior."""
    result = execute_admin_command(collection, {"usersInfo": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support usersInfo command")
