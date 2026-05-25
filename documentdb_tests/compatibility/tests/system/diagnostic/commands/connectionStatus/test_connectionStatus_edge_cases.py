"""Tests for connectionStatus command edge cases."""

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import IsType

pytestmark = pytest.mark.admin


def test_connectionStatus_immediately_after_connect(collection):
    """Test connectionStatus works immediately after connection."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed immediately")


def test_connectionStatus_user_with_no_roles(collection):
    """Test connectionStatus for connection without explicit roles returns arrays."""
    result = execute_admin_command(collection, {"connectionStatus": 1})
    assertResult(
        result,
        expected={"authInfo": {"authenticatedUserRoles": IsType("array")}},
        raw_res=True,
        msg="authenticatedUserRoles should be array even with no roles",
    )
