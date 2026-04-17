"""
Smoke test for killOp command.

Tests basic killOp functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_killOp(collection):
    """Test basic killOp behavior."""
    result = execute_admin_command(collection, {"killOp": 1, "op": 999999999})

    expected = {"ok": 1.0, "info": "attempting to kill op"}
    assertSuccessPartial(result, expected, msg="Should support killOp command")
