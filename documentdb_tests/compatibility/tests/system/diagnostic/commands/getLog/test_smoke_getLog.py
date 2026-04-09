"""
Smoke test for getLog command.

Tests basic getLog command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_getLog(collection):
    """Test basic getLog command behavior."""
    result = execute_admin_command(collection, {"getLog": "global"})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support getLog command")
