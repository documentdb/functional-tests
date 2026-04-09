"""
Smoke test for killSessions command.

Tests basic killSessions command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_killSessions(collection):
    """Test basic killSessions command behavior."""
    result = execute_command(collection, {"killSessions": []})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support killSessions command")
