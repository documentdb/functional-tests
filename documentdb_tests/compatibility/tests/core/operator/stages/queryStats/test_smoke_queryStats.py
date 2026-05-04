"""
Smoke test for $queryStats stage.

Tests basic $queryStats stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_queryStats(collection):
    """Test basic $queryStats stage behavior."""
    result = execute_admin_command(
        collection, {"aggregate": 1, "pipeline": [{"$queryStats": {}}], "cursor": {}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $queryStats stage")
