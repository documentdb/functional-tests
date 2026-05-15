"""
Smoke test for lockInfo command.

Tests basic lockInfo functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_lockInfo(collection):
    """Test basic lockInfo behavior."""
    result = execute_admin_command(collection, {"lockInfo": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support lockInfo command")
