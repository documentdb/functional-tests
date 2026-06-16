"""Tests for lockInfo command core behavior.

Verifies that lockInfo succeeds on admin database and returns a lockInfo array.
"""

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import IsType

pytestmark = pytest.mark.admin


def test_lockInfo_returns_ok(collection):
    """Test lockInfo returns ok:1 on admin database."""
    result = execute_admin_command(collection, {"lockInfo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="lockInfo should return ok:1")


def test_lockInfo_returns_lockInfo_array(collection):
    """Test lockInfo response contains a lockInfo array field."""
    result = execute_admin_command(collection, {"lockInfo": 1})
    assertProperties(
        result, {"lockInfo": IsType("array")}, msg="lockInfo field should be array", raw_res=True
    )
