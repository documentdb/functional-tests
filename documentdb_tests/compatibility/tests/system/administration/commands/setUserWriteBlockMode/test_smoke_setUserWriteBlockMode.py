"""
Smoke test for setUserWriteBlockMode command.

Tests basic setUserWriteBlockMode functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_setUserWriteBlockMode(collection):
    """Test basic setUserWriteBlockMode behavior."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support setUserWriteBlockMode command")
