"""Tests for buildInfo command error conditions.

Validates that invalid usages of buildInfo produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.commands.utils.diagnostic_test_case import (  # noqa: E501
    DiagnosticErrorTest,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import COMMAND_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticErrorTest] = [
    DiagnosticErrorTest(
        id="as_aggregation_stage",
        command={"aggregate": "test", "pipeline": [{"$buildInfo": {}}], "cursor": {}},
        use_admin=False,
        error_code=40324,
        msg="$buildInfo is not a valid aggregation stage",
    ),
    DiagnosticErrorTest(
        id="case_sensitive",
        command={"BuildInfo": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Case-mismatched command name should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_buildInfo_error_conditions(collection, test):
    """Verifies buildInfo rejects invalid usages with appropriate error codes."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
