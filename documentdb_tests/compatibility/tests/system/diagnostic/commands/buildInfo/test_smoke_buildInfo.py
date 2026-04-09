"""
Smoke test for buildInfo command.

Tests basic buildInfo command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_buildInfo(collection):
    """Test basic buildInfo command behavior."""
    result = execute_admin_command(collection, {"buildInfo": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support buildInfo command")
