"""
Smoke test for fsyncUnlock command.

Tests basic fsyncUnlock functionality by first locking with fsync,
then unlocking with fsyncUnlock.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_fsyncUnlock(collection):
    """Test basic fsyncUnlock behavior."""
    # Lock first
    execute_admin_command(collection, {"fsync": 1, "lock": True})

    # Unlock
    result = execute_admin_command(collection, {"fsyncUnlock": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support fsyncUnlock command")
