"""Tests for getClusterParameter authorization and namespace enforcement.

getClusterParameter is an admin-only command guarded by the
``getClusterParameter`` privilege action. The cases that run without
authentication are covered here: the command is rejected against any
non-admin database (namespace delegation), and it succeeds on admin when auth
is disabled.

DEFERRED (require an auth-enabled environment, not available on this target):
- A user holding the getClusterParameter action succeeds (#5, #7).
- A user lacking the action fails with an authorization error (#3, #5, #7).
- The read (getClusterParameter) action without the setClusterParameter action
  still permits reads (#18).
- A role scoped to a non-admin database does not grant this cluster-scoped
  action (#18).
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import UNAUTHORIZED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.rbac]


def test_getClusterParameter_rejected_on_non_admin_database(collection):
    """Test getClusterParameter is rejected against a non-admin database."""
    result = execute_command(collection, {"getClusterParameter": "*"})
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="getClusterParameter should be rejected on a non-admin database.",
    )


def test_getClusterParameter_succeeds_on_admin_without_auth(collection):
    """Test getClusterParameter succeeds on admin when authentication is disabled."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="getClusterParameter should succeed on admin with auth disabled.",
    )
