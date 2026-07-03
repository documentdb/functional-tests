"""Tests for buildInfo command consistency and database independence.

Validates that buildInfo returns consistent results across calls,
databases, and is unaffected by server settings.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = pytest.mark.admin


def test_buildInfo_idempotent(collection):
    """Test calling buildInfo multiple times returns identical results."""
    result1 = execute_admin_command(collection, {"buildInfo": 1})
    result2 = execute_admin_command(collection, {"buildInfo": 1})
    assertSuccess(result2, expected=result1, msg="Should return identical results", raw_res=True)


def test_buildInfo_any_database(collection):
    """Test buildInfo can be run on any database (not just admin)."""
    result = execute_command(collection, {"buildInfo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed on non-admin db")


def test_buildInfo_same_result_any_database(collection):
    """Test buildInfo returns same result from admin and non-admin database."""
    admin_result = execute_admin_command(collection, {"buildInfo": 1})
    db_result = execute_command(collection, {"buildInfo": 1})
    assertSuccess(
        db_result,
        expected=admin_result,
        msg="Should return same result from any database",
        raw_res=True,
    )


def test_buildInfo_nonexistent_database(collection):
    """Test buildInfo succeeds when run on a non-existent database."""
    other_db = f"{collection.name}_nonexistent_db"
    other_col = collection.database.client[other_db][collection.name]
    result = execute_command(other_col, {"buildInfo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed on non-existent database")
