"""Tests for connectionStatus response structure validation.

Validates response fields, types, and auth-related properties.
Note: Many auth-related tests require creating users with specific roles
and authenticating as them. These tests cover what's testable without
special RBAC setup (unauthenticated/default connection behavior).
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticPropertyTest,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, Len

pytestmark = pytest.mark.admin


RESPONSE_PROPERTY_TESTS: list[DiagnosticPropertyTest] = [
    DiagnosticPropertyTest(
        id="authenticatedUsers_is_array",
        checks={"authInfo": {"authenticatedUsers": IsType("array")}},
        msg="authenticatedUsers should be array",
    ),
    DiagnosticPropertyTest(
        id="authenticatedUserRoles_is_array",
        checks={"authInfo": {"authenticatedUserRoles": IsType("array")}},
        msg="authenticatedUserRoles should be array",
    ),
    DiagnosticPropertyTest(
        id="authInfo_exists",
        checks={"authInfo": Exists()},
        msg="authInfo should always exist",
    ),
    DiagnosticPropertyTest(
        id="unauthenticated_users_empty",
        checks={"authInfo": {"authenticatedUsers": Len(0)}},
        msg="without auth, authenticatedUsers should be empty",
    ),
    DiagnosticPropertyTest(
        id="unauthenticated_roles_empty",
        checks={"authInfo": {"authenticatedUserRoles": Len(0)}},
        msg="without auth, authenticatedUserRoles should be empty",
    ),
    DiagnosticPropertyTest(
        id="uuid_is_binData",
        checks={"uuid": IsType("binData")},
        msg="uuid should be a binData (UUID) field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_PROPERTY_TESTS))
def test_connectionStatus_response_properties(collection, test):
    """Verifies connectionStatus response fields and types."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_connectionStatus_succeeds_on_nonexistent_database(collection):
    """Test connectionStatus succeeds on a non-existent database."""
    other_col = collection.database.client["nonexistent_db_for_connstatus_test"]["dummy"]
    result = execute_command(other_col, {"connectionStatus": 1})
    assertProperties(
        result,
        {"ok": Exists(), "authInfo": Exists()},
        msg="connectionStatus should succeed on non-existent database",
        raw_res=True,
    )


def test_connectionStatus_same_result_across_databases(collection):
    """Test connectionStatus returns same authInfo on admin vs other database."""
    admin_result = execute_admin_command(collection, {"connectionStatus": 1})
    other_col = collection.database.client["nonexistent_db_for_connstatus_test"]["dummy"]
    other_result = execute_command(other_col, {"connectionStatus": 1})
    assertResult(
        other_result,
        expected={"authInfo": Eq(admin_result["authInfo"])},
        msg="authInfo should be identical across databases",
        raw_res=True,
    )
