"""
Smoke test for ping command.

Tests basic ping command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_ping(collection):
    """Test basic ping command behavior."""
    result = execute_admin_command(collection, {"ping": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support ping command")
