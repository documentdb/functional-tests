"""
Smoke test for startSession command.

Tests basic startSession command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_startSession(collection):
    """Test basic startSession command behavior."""
    result = execute_command(collection, {"startSession": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support startSession command")
