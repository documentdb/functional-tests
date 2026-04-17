"""
Smoke test for getCmdLineOpts command.

Tests basic getCmdLineOpts command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_getCmdLineOpts(collection):
    """Test basic getCmdLineOpts command behavior."""
    result = execute_admin_command(collection, {"getCmdLineOpts": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support getCmdLineOpts command")
