"""Tests for hostInfo command error conditions.

Validates that invalid usages of hostInfo produce the appropriate error codes.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="unrecognized_field",
        command={"hostInfo": 1, "unknownField": 1},
        use_admin=True,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject unrecognized fields",
    ),
    DiagnosticTestCase(
        id="case_sensitive",
        command={"HostInfo": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Case-mismatched command name should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_hostInfo_error_conditions(collection, test):
    """Verifies hostInfo rejects invalid usages with appropriate error codes."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
