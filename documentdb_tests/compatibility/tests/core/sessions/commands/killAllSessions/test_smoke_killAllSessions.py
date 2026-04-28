"""
Smoke test for killAllSessions command.

Tests basic killAllSessions command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_killAllSessions(collection):
    """Test basic killAllSessions command behavior."""
    result = execute_command(collection, {"killAllSessions": []})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support killAllSessions command")
