"""
Smoke test for usersInfo command.

Tests basic usersInfo functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_usersInfo(collection):
    """Test basic usersInfo behavior."""
    result = execute_admin_command(collection, {"usersInfo": 1})

    assertCommandSupported(result, msg="Should support usersInfo command")
