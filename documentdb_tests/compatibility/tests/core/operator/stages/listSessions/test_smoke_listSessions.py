"""
Smoke test for $listSessions stage.

Tests basic $listSessions stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_listSessions(collection):
    """Test basic $listSessions stage behavior."""
    # $listSessions must run against config.system.sessions
    config_db = collection.database.client["config"]
    system_sessions = config_db["system.sessions"]

    result = execute_command(
        system_sessions,
        {"aggregate": "system.sessions", "pipeline": [{"$listSessions": {}}], "cursor": {}},
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $listSessions stage")
