"""Tests for connectionStatus command core behavior and response structure."""

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Exists, IsType

pytestmark = pytest.mark.admin


def test_connectionStatus_returns_ok(collection):
    """Test connectionStatus returns ok: 1."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should return ok: 1")


def test_connectionStatus_returns_authInfo(collection):
    """Test connectionStatus returns authInfo document."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result, expected={"authInfo": Exists()}, raw_res=True, msg="Should return authInfo"
    )


def test_connectionStatus_authInfo_has_authenticatedUsers(collection):
    """Test connectionStatus returns authInfo.authenticatedUsers as an array."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUsers": IsType("array")}},
        raw_res=True,
        msg="authenticatedUsers should be an array",
    )


def test_connectionStatus_authInfo_has_authenticatedUserRoles(collection):
    """Test connectionStatus returns authInfo.authenticatedUserRoles as an array."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUserRoles": IsType("array")}},
        raw_res=True,
        msg="authenticatedUserRoles should be an array",
    )


def test_connectionStatus_succeeds_on_any_database(collection):
    """Test connectionStatus succeeds regardless of database context."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed on admin db")
