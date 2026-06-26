"""Tests for getClusterParameter authorization and namespace enforcement.

Verifies admin-only restriction and access-control delegation:
non-admin databases are rejected with Unauthorized, and the command
succeeds when auth is disabled (the default test environment).

Categories: #3 (non-admin-db + unauthorized), #5, #7 (auth), #18
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import UNAUTHORIZED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.rbac]


# ---------------------------------------------------------------------------
# §3 / §5 / §7  Admin-database restriction
# ---------------------------------------------------------------------------


def test_getClusterParameter_rejected_on_non_admin_database(collection):
    """Test getClusterParameter is rejected against a non-admin database."""
    result = execute_command(collection, {"getClusterParameter": "*"})
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="getClusterParameter should be rejected on a non-admin database.",
    )


# ---------------------------------------------------------------------------
# §5 / §7  Auth-disabled: admin succeeds (foundational delegation — one case)
# ---------------------------------------------------------------------------


def test_getClusterParameter_admin_succeeds_without_auth(collection):
    """Test getClusterParameter on admin database succeeds when auth is disabled."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="getClusterParameter on admin should succeed without auth"
    )
