"""Tests for connectionStatus authenticated users and roles.

Note: Many auth-related tests require creating users with specific roles
and authenticating as them. These tests cover what's testable without
special RBAC setup (unauthenticated/default connection behavior).
"""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Exists, IsType

pytestmark = pytest.mark.admin


def test_connectionStatus_authenticatedUsers_is_array(collection):
    """Test authenticatedUsers is an array."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUsers": IsType("array")}},
        raw_res=True,
        msg="authenticatedUsers should be array",
    )


def test_connectionStatus_authenticatedUserRoles_is_array(collection):
    """Test authenticatedUserRoles is an array."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUserRoles": IsType("array")}},
        raw_res=True,
        msg="authenticatedUserRoles should be array",
    )


def test_connectionStatus_showPrivileges_returns_privileges_array(collection):
    """Test showPrivileges: true returns authenticatedUserPrivileges as array."""
    result = execute_admin_command(collection, {"connectionStatus": 1, "showPrivileges": True})
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        raw_res=True,
        msg="authenticatedUserPrivileges should be array",
    )


def test_connectionStatus_authInfo_exists(collection):
    """Test authInfo document is always present."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result,
        expected={"authInfo": Exists()},
        raw_res=True,
        msg="authInfo should always exist",
    )
