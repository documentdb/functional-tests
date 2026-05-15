"""
Smoke test for commitTransaction command.

Tests basic commitTransaction command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailure
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_commitTransaction(collection):
    """Test basic commitTransaction command behavior."""
    result = execute_admin_command(collection, {"commitTransaction": 1})

    expected_error = {"code": 125, "msg": "commitTransaction must be run within a transaction"}
    assertFailure(result, expected_error, msg="Should support commitTransaction command")
