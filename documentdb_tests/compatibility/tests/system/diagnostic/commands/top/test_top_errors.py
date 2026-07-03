"""Tests for top command error conditions.

Validates that invalid usages of top produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import COMMAND_NOT_FOUND_ERROR, UNAUTHORIZED_ERROR
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

# Property [Admin Database Required]: top fails on non-admin database.
ADMIN_DB_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="non_admin_db",
        command={"top": 1},
        use_admin=False,
        error_code=UNAUTHORIZED_ERROR,
        msg="top should fail on non-admin db",
    ),
]

ERROR_TESTS = CASE_SENSITIVITY_TESTS + ADMIN_DB_TESTS


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_top_error_conditions(collection, test):
    """Test that invalid top command usages produce appropriate errors."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
