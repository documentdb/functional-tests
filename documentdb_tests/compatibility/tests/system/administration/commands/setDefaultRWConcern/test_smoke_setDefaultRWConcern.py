"""
Smoke test for setDefaultRWConcern command.

Tests basic setDefaultRWConcern functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_setDefaultRWConcern(collection):
    """Test basic setDefaultRWConcern behavior."""
    result = execute_admin_command(
        collection, {"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "local"}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support setDefaultRWConcern command")
