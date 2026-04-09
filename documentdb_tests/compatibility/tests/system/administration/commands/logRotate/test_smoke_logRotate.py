"""
Smoke test for logRotate command.

Tests basic logRotate functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_logRotate(collection):
    """Test basic logRotate behavior."""
    result = execute_admin_command(collection, {"logRotate": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support logRotate command")
