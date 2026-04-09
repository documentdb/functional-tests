"""
Smoke test for dropConnections command.

Tests basic dropConnections functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_dropConnections(collection):
    """Test basic dropConnections behavior."""
    result = execute_admin_command(collection, {"dropConnections": 1, "hostAndPort": []})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support dropConnections command")
