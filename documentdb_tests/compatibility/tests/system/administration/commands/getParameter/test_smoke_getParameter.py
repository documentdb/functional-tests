"""
Smoke test for getParameter command.

Tests basic getParameter functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_getParameter(collection):
    """Test basic getParameter behavior."""
    result = execute_admin_command(collection, {"getParameter": "*"})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support getParameter command")
