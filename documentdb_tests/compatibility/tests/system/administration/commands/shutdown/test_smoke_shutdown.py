"""
Smoke test for shutdown command.

Tests basic shutdown functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailure
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_shutdown(collection):
    """Test basic shutdown behavior."""
    result = execute_admin_command(collection, {"shutdown": 1, "force": False, "timeoutSecs": 0.0})

    expected = {"code": 13, "msg": "shutdown must run from localhost when running db without auth"}
    assertFailure(result, expected, msg="Should support shutdown command")
