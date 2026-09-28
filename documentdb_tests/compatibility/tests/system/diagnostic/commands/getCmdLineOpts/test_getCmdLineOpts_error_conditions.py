"""Tests for getCmdLineOpts command error conditions.

Validates that invalid usages of getCmdLineOpts produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    UNAUTHORIZED_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="non_admin_database",
        command={"getCmdLineOpts": 1},
        use_admin=False,
        error_code=UNAUTHORIZED_ERROR,
        msg="getCmdLineOpts may only be run against the admin database",
    ),
    DiagnosticTestCase(
        id="unrecognized_field",
        command={"getCmdLineOpts": 1, "unknownField": 1},
        use_admin=True,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject unrecognized fields",
    ),
    DiagnosticTestCase(
        id="case_sensitive",
        command={"GetCmdLineOpts": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Case-mismatched command name should fail",
    ),
    DiagnosticTestCase(
        id="as_aggregation_stage",
        command={"aggregate": "test", "pipeline": [{"$getCmdLineOpts": {}}], "cursor": {}},
        use_admin=False,
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="$getCmdLineOpts is not a valid aggregation stage",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_getCmdLineOpts_error_conditions(collection, test):
    """Verifies getCmdLineOpts rejects invalid usages with appropriate error codes."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
