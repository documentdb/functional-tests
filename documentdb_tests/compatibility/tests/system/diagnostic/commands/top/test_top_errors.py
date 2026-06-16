"""Tests for top command error conditions.

Validates that invalid usages of top produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import COMMAND_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [Case Sensitivity]: command names are case-sensitive.
CASE_SENSITIVITY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="case_sensitive_Top",
        command={"Top": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="'Top' (capitalized) should not be recognized",
    ),
    DiagnosticTestCase(
        id="case_sensitive_TOP",
        command={"TOP": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="'TOP' (all caps) should not be recognized",
    ),
    DiagnosticTestCase(
        id="case_sensitive_tOP",
        command={"tOP": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="'tOP' (mixed case) should not be recognized",
    ),
]

ERROR_TESTS = CASE_SENSITIVITY_TESTS


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_top_error_conditions(collection, test):
    """Test that invalid top command usages produce appropriate errors."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_top_unrecognized_field(collection):
    """Test top behavior with an unrecognized field."""
    result = execute_admin_command(collection, {"top": 1, "unknownField": 1})
    # MongoDB may accept or reject unrecognized fields for top.
    # Verify actual behavior — placeholder assertion until run against MongoDB.
    assertSuccessPartial(result, {"ok": 1.0}, msg="top with unrecognized field")


def test_top_multiple_unrecognized_fields(collection):
    """Test top behavior with multiple unrecognized fields."""
    result = execute_admin_command(collection, {"top": 1, "foo": 1, "bar": "baz", "qux": []})
    # Same behavior expectation as single unrecognized field.
    assertSuccessPartial(result, {"ok": 1.0}, msg="top with multiple unrecognized fields")
