"""
Smoke test for listCommands command.

Tests basic listCommands command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_listCommands(collection):
    """Test basic listCommands command behavior."""
    result = execute_admin_command(collection, {"listCommands": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support listCommands command")
