"""Tests for whatsmyuri command error conditions.

Validates that invalid usages of whatsmyuri produce appropriate errors.
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


# Property [Case Sensitivity]: whatsmyuri is case-sensitive and rejects mismatched casing.
CASE_SENSITIVITY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="case_sensitive_capital_w",
        command={"WhatsMyUri": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="whatsmyuri should reject camel-cased command name",
    ),
    DiagnosticTestCase(
        id="case_sensitive_all_upper",
        command={"WHATSMYURI": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="whatsmyuri should reject all-uppercase command name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CASE_SENSITIVITY_TESTS))
def test_whatsmyuri_error_conditions(collection, test):
    """Test whatsmyuri error conditions."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Not a Pipeline Stage]: whatsmyuri is not usable as an aggregation stage.
def test_whatsmyuri_as_aggregation_stage(collection):
    """Test whatsmyuri is rejected as an aggregation pipeline stage."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$whatsmyuri": {}}],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="whatsmyuri should not be usable as an aggregation stage",
    )
