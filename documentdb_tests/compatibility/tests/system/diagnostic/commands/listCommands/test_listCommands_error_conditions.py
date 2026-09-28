"""Tests for listCommands command error conditions.

Validates that invalid usages of listCommands produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="as_aggregation_stage",
        command={"aggregate": "test", "pipeline": [{"$listCommands": {}}], "cursor": {}},
        use_admin=False,
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="$listCommands is not a valid aggregation stage",
    ),
    DiagnosticTestCase(
        id="case_sensitive",
        command={"ListCommands": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Case-mismatched command name should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_listCommands_error_conditions(collection, test):
    """Verifies listCommands rejects invalid usages with appropriate error codes."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
