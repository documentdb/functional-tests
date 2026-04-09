"""
Smoke test for refreshSessions command.

Tests basic refreshSessions command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_refreshSessions(collection):
    """Test basic refreshSessions command behavior."""
    result = execute_command(collection, {"refreshSessions": []})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support refreshSessions command")
