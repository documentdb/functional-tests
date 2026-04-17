"""
Smoke test for autoCompact command.

Tests basic autoCompact functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_autoCompact(collection):
    """Test basic autoCompact behavior."""
    result = execute_admin_command(collection, {"autoCompact": True})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support autoCompact command")
