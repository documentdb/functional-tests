"""Tests for serverStatus command error conditions.

Validates that invalid usages of serverStatus produce appropriate errors.
serverStatus is highly permissive: it accepts any BSON type as the command
argument value, ignores unrecognized fields, and coerces toggle values to
truthy/falsy. The only error condition is a case-mismatched command name,
which is the generic unknown-command rejection, not serverStatus-specific.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import COMMAND_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [Case Sensitivity]: serverStatus command name is case-sensitive.
ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="case_ServerStatus",
        command={"ServerStatus": 1},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="serverStatus should reject case-mismatched command name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_serverStatus_error_conditions(collection, test):
    """Verify serverStatus rejects invalid usages with appropriate error codes."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
