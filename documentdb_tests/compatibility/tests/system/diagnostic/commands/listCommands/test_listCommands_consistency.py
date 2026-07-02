"""Tests for listCommands command consistency and availability.

Validates that listCommands works across databases and returns consistent results.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


DATABASE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="admin_database",
        command={"listCommands": 1},
        use_admin=True,
        checks={"ok": Eq(1.0)},
        msg="Should succeed on admin database",
    ),
    DiagnosticTestCase(
        id="non_admin_database",
        command={"listCommands": 1},
        use_admin=False,
        checks={"ok": Eq(1.0)},
        msg="Should succeed on non-admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATABASE_TESTS))
def test_listCommands_database_availability(collection, test):
    """Test listCommands works on both admin and non-admin databases."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_listCommands_nonexistent_database(collection):
    """Test listCommands succeeds when run on a non-existent database."""
    other_db = f"{collection.name}_nonexistent_db"
    other_col = collection.database.client[other_db][collection.name]
    result = execute_command(other_col, {"listCommands": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed on non-existent database")


def test_listCommands_idempotent(collection):
    """Test calling listCommands multiple times returns identical results."""
    result1 = execute_admin_command(collection, {"listCommands": 1})
    result2 = execute_admin_command(collection, {"listCommands": 1})
    assertSuccess(result2, expected=result1, msg="Should return identical results", raw_res=True)


def test_listCommands_same_result_any_database(collection):
    """Test listCommands returns same result from admin and non-admin database."""
    admin_result = execute_admin_command(collection, {"listCommands": 1})
    db_result = execute_command(collection, {"listCommands": 1})
    assertSuccess(
        db_result,
        expected=admin_result,
        msg="Should return same result from any database",
        raw_res=True,
    )
