"""
Smoke test for connectionStatus command.

Tests basic connectionStatus command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_connectionStatus(collection):
    """Test basic connectionStatus command behavior."""
    result = execute_admin_command(collection, {"connectionStatus": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support connectionStatus command")
