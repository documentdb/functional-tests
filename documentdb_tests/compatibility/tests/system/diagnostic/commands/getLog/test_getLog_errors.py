"""Tests for getLog command error conditions.

Covers invalid log component names (unknown component, the deprecated "rs"
value, empty string), unrecognized command fields, and the admin-database
requirement.

BSON type rejection/acceptance for the value is covered in
test_getLog_argument_validation.py.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    OPERATION_FAILED_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# An unknown, deprecated, or empty log component name fails with OperationFailed.
ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "unknown_component",
        command={"getLog": "invalid"},
        error_code=OPERATION_FAILED_ERROR,
        msg="Unknown log component name should error",
    ),
    DiagnosticTestCase(
        "deprecated_rs",
        command={"getLog": "rs"},
        error_code=OPERATION_FAILED_ERROR,
        msg="Deprecated 'rs' value should error",
    ),
    DiagnosticTestCase(
        "empty_string",
        command={"getLog": ""},
        error_code=OPERATION_FAILED_ERROR,
        msg="Empty string component should error",
    ),
    DiagnosticTestCase(
        "unrecognized_field",
        command={"getLog": "global", "unknownField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized command field should error",
    ),
    DiagnosticTestCase(
        "non_admin_database",
        command={"getLog": "global"},
        use_admin=False,
        error_code=UNAUTHORIZED_ERROR,
        msg="getLog should only run on the admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_getLog_error(collection, test):
    """Test getLog returns the expected error code for invalid arguments."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
