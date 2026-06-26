"""Tests for getClusterParameter authorization and namespace enforcement.

Verifies admin-only restriction and access-control delegation:
non-admin databases are rejected with Unauthorized, and the command
succeeds when auth is disabled (the default test environment).

Categories: #3 (non-admin-db + unauthorized), #5, #7 (auth), #18
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import UNAUTHORIZED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# ---------------------------------------------------------------------------
# §3 / §5 / §7  Admin-database restriction
# ---------------------------------------------------------------------------

# Non-admin databases reject getClusterParameter with Unauthorized (code 13).
# We run via execute_command() (which uses the fixture's own non-admin database)
# to target a non-admin context without bypassing the executor restriction.
_NON_ADMIN_DB_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="user_db",
        command={"getClusterParameter": "*"},
        use_admin=False,
        error_code=UNAUTHORIZED_ERROR,
        msg="getClusterParameter on a non-admin user database should fail with Unauthorized",
    ),
]


@pytest.mark.parametrize("test", pytest_params(_NON_ADMIN_DB_TESTS))
def test_getClusterParameter_non_admin_db_rejected(collection, test):
    """Test getClusterParameter fails with Unauthorized on non-admin databases."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# §5 / §7  Auth-disabled: admin succeeds (foundational delegation — one case)
# ---------------------------------------------------------------------------


def test_getClusterParameter_admin_succeeds_without_auth(collection):
    """Test getClusterParameter on admin database succeeds when auth is disabled."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="getClusterParameter on admin should succeed without auth"
    )
