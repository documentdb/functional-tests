"""
Smoke test for connPoolStats command.

Tests basic connPoolStats command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_connPoolStats(collection):
    """Test basic connPoolStats command behavior."""
    result = execute_admin_command(collection, {"connPoolStats": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support connPoolStats command")
