"""Tests for dbStats command core behavior.

Covers success on populated and empty databases, the all-zero response for
a non-existent database, and execution against the admin database.
Command-level errors are in test_dbStats_errors.py.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType
from documentdb_tests.framework.target_collection import TargetDatabase

pytestmark = pytest.mark.admin


SUCCESS_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="populated_database",
        setup=[{"insert": "c1", "documents": [{"_id": 0, "a": 1}, {"_id": 1, "a": 2}]}],
        command={"dbStats": 1},
        use_admin=False,
        checks={"ok": Eq(1.0), "db": IsType("string")},
        msg="Populated database should return ok:1",
    ),
    DiagnosticTestCase(
        id="empty_database",
        command={"dbStats": 1},
        use_admin=False,
        checks={"ok": Eq(1.0), "db": IsType("string"), "collections": Eq(Int64(0))},
        msg="Empty database should return ok:1 with zero collections",
    ),
    DiagnosticTestCase(
        id="admin_database",
        command={"dbStats": 1},
        use_admin=True,
        checks={"ok": Eq(1.0), "db": Eq("admin")},
        msg="dbStats on admin database should report db:admin",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_dbStats_core_behavior(collection, test):
    """Test dbStats succeeds and reports expected top-level fields across databases."""
    for setup_command in test.setup:
        setup_result = execute_command(collection, setup_command)
        if isinstance(setup_result, Exception):
            raise setup_result
    executor = execute_admin_command if test.use_admin else execute_command
    result = executor(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


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
