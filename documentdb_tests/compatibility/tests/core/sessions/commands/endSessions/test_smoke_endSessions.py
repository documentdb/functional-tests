"""
Smoke test for endSessions command.

Tests basic endSessions command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_endSessions(collection):
    """Test basic endSessions command behavior."""
    result = execute_command(collection, {"endSessions": []})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support endSessions command")
