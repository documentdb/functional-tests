"""
Smoke test for killAllSessionsByPattern command.

Tests basic killAllSessionsByPattern command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_killAllSessionsByPattern(collection):
    """Test basic killAllSessionsByPattern command behavior."""
    result = execute_command(collection, {"killAllSessionsByPattern": []})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support killAllSessionsByPattern command")
