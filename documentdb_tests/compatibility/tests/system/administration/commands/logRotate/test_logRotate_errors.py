"""Tests for logRotate command error cases."""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.admin_test_case import (
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    NO_SUCH_KEY_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


INVALID_STRING_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "invalid_string",
        command={"logRotate": "invalid"},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Should reject invalid string value",
    ),
    AdminTestCase(
        "empty_string",
        command={"logRotate": ""},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Should reject empty string",
    ),
    AdminTestCase(
        "case_sensitive_SERVER",
        command={"logRotate": "SERVER"},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Should reject uppercase SERVER (case-sensitive)",
    ),
    AdminTestCase(
        "case_sensitive_Audit",
        command={"logRotate": "Audit"},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Should reject mixed-case Audit (case-sensitive)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_STRING_TESTS))
def test_logRotate_invalid_arguments(collection, test):
    """Test that logRotate rejects invalid string values."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_logRotate_unrecognized_field(collection):
    """Test that logRotate rejects unrecognized top-level fields."""
    result = execute_admin_command(collection, {"logRotate": 1, "unknownField": 1})
    assertFailureCode(
        result, UNRECOGNIZED_COMMAND_FIELD_ERROR, msg="Should reject unrecognized fields"
    )


def test_logRotate_non_admin_database(collection):
    """Test that logRotate fails when run on a non-admin database."""
    result = execute_command(collection, {"logRotate": 1})
    assertFailureCode(result, UNAUTHORIZED_ERROR, msg="Should fail on non-admin database")


def test_logRotate_audit_target_rejected_when_disabled(collection):
    """Test that the 'audit' log target is rejected when auditing is disabled."""
    result = execute_admin_command(collection, {"logRotate": "audit"})
    assertFailureCode(
        result, NO_SUCH_KEY_ERROR, msg="Should reject audit target when auditing is disabled"
    )
