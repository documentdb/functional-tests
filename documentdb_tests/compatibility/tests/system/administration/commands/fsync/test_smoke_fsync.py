"""
Smoke test for fsync command.

Tests basic fsync functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_fsync(collection):
    """Test basic fsync behavior."""
    result = execute_admin_command(collection, {"fsync": 1})

    expected = {"ok": 1.0, "numFiles": 1}
    assertSuccessPartial(result, expected, msg="Should support fsync command")
