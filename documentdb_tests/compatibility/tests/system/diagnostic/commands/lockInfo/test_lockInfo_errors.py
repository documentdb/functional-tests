"""Tests for lockInfo command error cases.

Verifies that lockInfo returns correct error codes when run on non-admin
database or with unrecognized fields.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="non_admin_database",
        command={"lockInfo": 1},
        use_admin=False,
        error_code=UNAUTHORIZED_ERROR,
        msg="lockInfo on non-admin db should be unauthorized",
    ),
    DiagnosticTestCase(
        id="unrecognized_field",
        command={"lockInfo": 1, "foo": 1},
        use_admin=True,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should error",
    ),
    DiagnosticTestCase(
        id="wrong_case",
        command={"LockInfo": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Command name is case-sensitive; 'LockInfo' should not be found",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_lockInfo_error_conditions(collection, test):
    """Verifies lockInfo returns appropriate error codes for invalid usages."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
