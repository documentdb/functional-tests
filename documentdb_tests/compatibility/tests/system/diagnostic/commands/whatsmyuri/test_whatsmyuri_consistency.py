"""Tests for whatsmyuri command consistency and database independence.

Validates that whatsmyuri returns consistent results across calls,
databases, and is unaffected by server settings.
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


# Property [Database Independence]: whatsmyuri succeeds on any database.
DATABASE_INDEPENDENCE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "any_database",
        command={"whatsmyuri": 1},
        use_admin=False,
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should succeed on non-admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATABASE_INDEPENDENCE_TESTS))
def test_whatsmyuri_consistency(collection, test):
    """Test whatsmyuri consistency."""
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_whatsmyuri_idempotent(collection):
    """Test whatsmyuri idempotency."""
    result1 = execute_admin_command(collection, {"whatsmyuri": 1})
    result2 = execute_admin_command(collection, {"whatsmyuri": 1})
    assertSuccess(
        result2,
        expected=result1,
        msg="whatsmyuri should return identical results across calls",
        raw_res=True,
    )


def test_whatsmyuri_same_result_any_database(collection):
    """Test whatsmyuri returns same result from admin and non-admin database."""
    admin_result = execute_admin_command(collection, {"whatsmyuri": 1})
    db_result = execute_command(collection, {"whatsmyuri": 1})
    assertSuccess(
        db_result,
        expected=admin_result,
        msg="whatsmyuri should return same result from any database",
        raw_res=True,
    )


def test_whatsmyuri_nonexistent_database(collection):
    """Test whatsmyuri on a non-existent database."""
    other_db = f"{collection.name}_nonexistent_db"
    other_col = collection.database.client[other_db][collection.name]
    result = execute_command(other_col, {"whatsmyuri": 1})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="whatsmyuri should succeed on non-existent database",
    )
