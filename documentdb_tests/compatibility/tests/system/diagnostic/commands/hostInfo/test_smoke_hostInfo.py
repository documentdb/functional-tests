"""
Smoke test for hostInfo command.

Tests basic hostInfo command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_hostInfo(collection):
    """Test basic hostInfo command behavior."""
    result = execute_admin_command(collection, {"hostInfo": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support hostInfo command")
