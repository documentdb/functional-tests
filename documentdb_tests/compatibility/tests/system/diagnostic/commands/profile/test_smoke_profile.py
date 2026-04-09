"""
Smoke test for profile command.

Tests basic profile command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_profile(collection):
    """Test basic profile command behavior."""
    result = execute_command(collection, {"profile": 0})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support profile command")
