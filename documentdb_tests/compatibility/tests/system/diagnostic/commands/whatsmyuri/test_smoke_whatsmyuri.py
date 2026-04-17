"""
Smoke test for whatsmyuri command.

Tests basic whatsmyuri command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_whatsmyuri(collection):
    """Test basic whatsmyuri command behavior."""
    result = execute_admin_command(collection, {"whatsmyuri": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support whatsmyuri command")
