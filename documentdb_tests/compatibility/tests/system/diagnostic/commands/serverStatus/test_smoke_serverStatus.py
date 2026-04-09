"""
Smoke test for serverStatus command.

Tests basic serverStatus command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_serverStatus(collection):
    """Test basic serverStatus command behavior."""
    result = execute_admin_command(collection, {"serverStatus": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support serverStatus command")
