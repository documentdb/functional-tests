"""
Smoke test for getDefaultRWConcern command.

Tests basic getDefaultRWConcern functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_getDefaultRWConcern(collection):
    """Test basic getDefaultRWConcern behavior."""
    result = execute_admin_command(collection, {"getDefaultRWConcern": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support getDefaultRWConcern command")
