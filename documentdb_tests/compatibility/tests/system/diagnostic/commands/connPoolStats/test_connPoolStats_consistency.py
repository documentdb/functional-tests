"""Tests for connPoolStats connection count consistency."""

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Gte

pytestmark = pytest.mark.admin


def test_connPoolStats_repeated_calls(collection):
    """Test connPoolStats can be called repeatedly without error."""
    for _ in range(5):
        result = execute_admin_command(collection, {"connPoolStats": 1})
        assertSuccessPartial(result, {"ok": 1.0}, msg="Repeated call should succeed")


def test_connPoolStats_totalCreated_non_decreasing(collection):
    """Test totalCreated is monotonically non-decreasing across calls."""
    r1 = execute_admin_command(collection, {"connPoolStats": 1})
    created1 = r1["totalCreated"]
    r2 = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        r2,
        expected={"totalCreated": Gte(created1)},
        raw_res=True,
        msg="totalCreated should not decrease",
    )
