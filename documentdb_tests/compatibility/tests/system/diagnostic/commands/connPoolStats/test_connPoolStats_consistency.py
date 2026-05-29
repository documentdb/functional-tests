"""Tests for connPoolStats consistency and database context.

Verifies connection count invariants (totalCreated is non-decreasing,
totalCreated >= totalInUse + totalAvailable), repeated call stability,
and that the command succeeds regardless of database context.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.property_checks import Gte

pytestmark = pytest.mark.admin


def test_connPoolStats_repeated_calls(collection):
    """Verify connPoolStats can be called repeatedly without error."""
    for _ in range(5):
        result = execute_admin_command(collection, {"connPoolStats": 1})
        assertSuccessPartial(result, {"ok": 1.0}, msg="Repeated call should succeed")


def test_connPoolStats_totalCreated_non_decreasing(collection):
    """Verify totalCreated is monotonically non-decreasing across calls."""
    r1 = execute_admin_command(collection, {"connPoolStats": 1})
    created1 = r1.get("totalCreated", None)
    r2 = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        r2,
        expected={"totalCreated": Gte(created1)},
        raw_res=True,
        msg="totalCreated should not decrease",
    )


def test_connPoolStats_totalCreated_gte_inUse_plus_available(collection):
    """Verify totalCreated >= totalInUse + totalAvailable."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    minimum = result.get("totalInUse", None) + result.get("totalAvailable", None)
    assertResult(
        result,
        expected={"totalCreated": Gte(minimum)},
        raw_res=True,
        msg="totalCreated should be >= totalInUse + totalAvailable",
    )


def test_connPoolStats_succeeds_on_nonexistent_database(collection):
    """Verify connPoolStats succeeds when run on a non-existent database."""
    other_db = f"{collection.name}_nonexistent_db"
    other_col = collection.database.client[other_db][collection.name]
    result = execute_command(other_col, {"connPoolStats": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed on non-existent database")
