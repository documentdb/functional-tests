"""Smoke test for commitTransaction command."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_commitTransaction(collection):
    """Test basic commitTransaction command behavior."""
    result = execute_admin_command(collection, {"commitTransaction": 1})
    assertFailureCode(
        result,
        NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should fail with NoSuchTransaction outside a transaction",
    )
