"""
Smoke test for connectionStatus command.

Verifies the command executes successfully and returns ok: 1.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_connectionStatus(collection):
    """Verify connectionStatus executes successfully and returns ok: 1."""
    result = execute_admin_command(collection, {"connectionStatus": 1})

    assertCommandSupported(result, msg="Should support connectionStatus command")
