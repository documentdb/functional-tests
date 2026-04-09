"""
Smoke test for invalidateUserCache command.

Tests basic invalidateUserCache functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_invalidateUserCache(collection):
    """Test basic invalidateUserCache behavior."""
    result = execute_admin_command(collection, {"invalidateUserCache": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support invalidateUserCache command")
