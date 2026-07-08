"""Tests for ping command error conditions.

Validates that invalid usages of ping produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="unrecognized_field",
        command={"ping": 1, "unknownField": "test"},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject unrecognized fields",
    ),
    DiagnosticTestCase(
        id="case_sensitive",
        command={"Ping": 1},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Case-mismatched command name should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_ping_error_conditions(collection, test):
    """Verifies ping rejects invalid usages with appropriate error codes."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_ping_as_pipeline_stage(collection):
    """Test that $ping is not a valid aggregation pipeline stage."""
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$ping": 1}], "cursor": {}},
    )
    assertFailureCode(
        result, UNKNOWN_PIPELINE_STAGE_ERROR, msg="ping should not be a valid pipeline stage"
    )
