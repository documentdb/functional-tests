"""
Smoke test for abortTransaction command.

Tests basic abortTransaction command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailure
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_abortTransaction(collection):
    """Test basic abortTransaction command behavior."""
    result = execute_admin_command(collection, {"abortTransaction": 1})

    expected_error = {"code": 125, "msg": "abortTransaction must be run within a transaction"}
    assertFailure(result, expected_error, msg="Should support abortTransaction command")
