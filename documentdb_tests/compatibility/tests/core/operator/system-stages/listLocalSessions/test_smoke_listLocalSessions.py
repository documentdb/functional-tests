"""
Smoke test for $listLocalSessions system stage.

Tests basic $listLocalSessions system stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_listLocalSessions(collection):
    """Test basic $listLocalSessions system stage behavior."""
    result = execute_admin_command(
        collection, {"aggregate": 1, "pipeline": [{"$listLocalSessions": {}}], "cursor": {}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $listLocalSessions system stage")
