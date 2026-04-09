"""
Smoke test for setParameter command.

Tests basic setParameter functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_setParameter(collection):
    """Test basic setParameter behavior."""
    get_result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    original_value = get_result.get("logLevel", 0) if not isinstance(get_result, Exception) else 0

    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support setParameter command")

    execute_admin_command(collection, {"setParameter": 1, "logLevel": original_value})
