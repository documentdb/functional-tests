"""
Smoke test for logout command.

Tests basic logout functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_logout(collection):
    """Test basic logout behavior."""
    result = execute_command(collection, {"logout": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support logout command")
