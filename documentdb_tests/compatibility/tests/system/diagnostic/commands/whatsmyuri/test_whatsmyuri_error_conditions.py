"""Tests for whatsmyuri command error conditions.

Validates that invalid usages of whatsmyuri produce appropriate errors.
Uses CommandTestCase because the aggregation stage test needs ctx.collection
for the aggregate command.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [Case Sensitivity]: whatsmyuri is case-sensitive and rejects mismatched casing.
CASE_SENSITIVITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "case_sensitive_capital_w",
        command={"WhatsMyUri": 1},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="whatsmyuri should reject camel-cased command name",
    ),
    CommandTestCase(
        "case_sensitive_all_upper",
        command={"WHATSMYURI": 1},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="whatsmyuri should reject all-uppercase command name",
    ),
]

# Property [Not a Pipeline Stage]: whatsmyuri is not usable as an aggregation stage.
PIPELINE_STAGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "as_aggregation_stage",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$whatsmyuri": {}}],
            "cursor": {},
        },
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="whatsmyuri should not be usable as an aggregation stage",
    ),
]

ALL_TESTS = CASE_SENSITIVITY_TESTS + PIPELINE_STAGE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_whatsmyuri_error_conditions(collection, test):
    """Test whatsmyuri error conditions."""
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    # Case sensitivity tests target the admin db; the aggregate test does not.
    if next(iter(cmd)).lower() == "whatsmyuri":
        result = execute_admin_command(collection, cmd)
    else:
        result = execute_command(collection, cmd)
    assertResult(result, error_code=test.error_code, msg=test.msg)
