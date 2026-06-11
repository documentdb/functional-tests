"""
Smoke test for abortTransaction command.

Tests basic abortTransaction command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_abortTransaction(collection):
    """Test basic abortTransaction command behavior."""
    result = execute_admin_command(collection, {"abortTransaction": 1})
    assertFailureCode(
        result, NO_SUCH_TRANSACTION_ERROR, msg="Should support abortTransaction command"
    )
