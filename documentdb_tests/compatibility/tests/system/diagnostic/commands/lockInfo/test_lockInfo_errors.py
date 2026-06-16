"""Tests for lockInfo command error cases.

Verifies that lockInfo returns correct error codes when run on non-admin
database or with unrecognized fields.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import UNAUTHORIZED_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.admin


def test_lockInfo_non_admin_database_returns_unauthorized(collection):
    """Test lockInfo on non-admin database returns error code 13 (Unauthorized)."""
    result = execute_command(collection, {"lockInfo": 1})
    assertFailureCode(
        result, UNAUTHORIZED_ERROR, msg="lockInfo on non-admin db should be unauthorized"
    )
