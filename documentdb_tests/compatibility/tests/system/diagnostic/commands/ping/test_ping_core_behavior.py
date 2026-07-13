"""Tests for ping command core behavior.

Validates that ping succeeds on both admin and non-admin databases,
can be executed repeatedly in succession, and works after other commands
or write activity.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


DATABASE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="admin_database",
        command={"ping": 1},
        use_admin=True,
        checks={"ok": Eq(1.0)},
        msg="Should succeed on admin database",
    ),
    DiagnosticTestCase(
        id="non_admin_database",
        command={"ping": 1},
        use_admin=False,
        checks={"ok": Eq(1.0)},
        msg="Should succeed on non-admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATABASE_TESTS))
def test_ping_on_database(collection, test):
    """Test ping returns ok:1 on both admin and non-admin databases."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_ping_multiple_times_in_succession(collection):
    """Test ping can be executed multiple times in succession."""
    for _ in range(3):
        result = execute_admin_command(collection, {"ping": 1})
        assertProperties(
            result, {"ok": Eq(1.0)}, msg="Should succeed on repeated execution", raw_res=True
        )


def test_ping_after_write_activity(collection):
    """Test ping returns ok:1 immediately after write activity."""
    collection.insert_many([{"_id": i, "data": "x" * 100} for i in range(100)])
    result = execute_admin_command(collection, {"ping": 1})
    assertProperties(
        result, {"ok": Eq(1.0)}, msg="Should succeed after write activity", raw_res=True
    )
