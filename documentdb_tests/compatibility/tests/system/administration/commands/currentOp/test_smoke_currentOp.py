"""
Smoke test for currentOp command.

Tests basic currentOp functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_currentOp(collection):
    """Test basic currentOp behavior."""
    result = execute_admin_command(collection, {"currentOp": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support currentOp command")
