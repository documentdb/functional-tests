"""Tests for dbStats command core behavior.

Covers success on populated and empty databases, the all-zero response for
a non-existent database, execution against the admin database, and rejection
of unrecognized command fields.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.target_collection import TargetDatabase

pytestmark = pytest.mark.admin


def test_dbStats_populated_database_returns_ok(collection):
    """Test dbStats returns ok:1 on a database that has collections."""
    collection.insert_many([{"_id": 0, "a": 1}, {"_id": 1, "a": 2}])
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "db": collection.database.name},
        msg="Populated database should return ok:1",
    )


def test_dbStats_empty_database_returns_ok(collection):
    """Test dbStats returns ok:1 with zero collections on an empty database."""
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "db": collection.database.name, "collections": Int64(0)},
        msg="Empty database should return ok:1 with zero collections",
    )


def test_dbStats_nonexistent_database_returns_zeros(collection, register_db_cleanup):
    """Test dbStats on a non-existent database returns zeroed size and count fields."""
    missing_coll = TargetDatabase(suffix="missing").resolve(collection.database, collection)
    register_db_cleanup(missing_coll.database.name)
    result = execute_command(missing_coll, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {
            "ok": 1.0,
            "db": missing_coll.database.name,
            "collections": Int64(0),
            "objects": Int64(0),
            "storageSize": 0.0,
            "indexes": Int64(0),
            "indexSize": 0.0,
        },
        msg="Non-existent database should report all counts and sizes as zero",
    )


def test_dbStats_admin_database_reports_admin_name(collection):
    """Test dbStats executed against the admin database reports db:admin."""
    admin_coll = collection.database.client["admin"]["unused"]
    result = execute_command(admin_coll, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "db": "admin"},
        msg="dbStats on admin database should report db:admin",
    )


def test_dbStats_unrecognized_field_errors(collection):
    """Test dbStats rejects an unrecognized command field."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbStats": 1, "bogusField": 1})
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized command field should error with code 40415",
    )
