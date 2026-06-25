"""Tests for hostInfo core behavior and consistency.

Validates that hostInfo ignores its argument value and succeeds across
different database contexts.
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


ACCESS_TESTS = [
    # The MongoDB manual states hostInfo must be run against the admin database,
    # but in practice it succeeds on any database.
    DiagnosticTestCase(
        id="succeeds_on_non_admin_db",
        use_admin=False,
        checks={"ok": Eq(1.0)},
        msg="hostInfo should succeed on a non-admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ACCESS_TESTS))
def test_hostInfo_access(collection, test):
    """Verify hostInfo access behaviour across different database contexts."""
    if test.use_admin:
        result = execute_admin_command(collection, {"hostInfo": 1})
    else:
        result = execute_command(collection, {"hostInfo": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_hostInfo_argument_value_ignored(collection):
    """Verify the command value does not affect the os/extra output."""
    numeric = execute_admin_command(collection, {"hostInfo": 1})
    other = execute_admin_command(collection, {"hostInfo": "ignored"})
    assertProperties(
        other,
        {"os": Eq(numeric.get("os")), "extra": Eq(numeric.get("extra"))},
        raw_res=True,
        msg="hostInfo output should not depend on the command value",
    )
