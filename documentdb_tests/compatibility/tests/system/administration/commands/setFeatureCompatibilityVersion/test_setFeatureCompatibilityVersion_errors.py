"""Tests for setFeatureCompatibilityVersion error cases.

Covers admin-database-only enforcement, unknown/extra fields,
response structure, and setParameter rejection.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FCV_INVALID_VERSION_ERROR,
    ILLEGAL_OPERATION_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection):
    """Read the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return "8.2"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.2")
    return str(fcv_data)


# Property [Admin DB Accepted]: setFeatureCompatibilityVersion succeeds on the admin database.
ADMIN_DB_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "admin_db_accepted",
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed on the admin database",
    ),
]


# Property [User DB Rejected]: setFeatureCompatibilityVersion fails on a user database.
USER_DB_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "user_db_rejected",
        error_code=UNAUTHORIZED_ERROR,
        msg="setFeatureCompatibilityVersion should reject execution on a user database",
    ),
]


# Property [Unrecognized Fields]: setFeatureCompatibilityVersion rejects unrecognized fields.
UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_field",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setFeatureCompatibilityVersion should reject unrecognized fields",
    ),
    CommandTestCase(
        "misspelled_confirm",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confrim": True,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setFeatureCompatibilityVersion should reject misspelled 'confrim' as unknown field",
    ),
]


# Property [setParameter Rejected]: FCV cannot be set through setParameter.
SET_PARAMETER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "via_setParameter",
        command=lambda ctx: {"setParameter": 1, "featureCompatibilityVersion": "8.0"},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="setFeatureCompatibilityVersion should not be settable via setParameter",
    ),
]


# Property [Error Contains Code]: error response contains a numeric code.
ERROR_CODE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "invalid_version_error_code",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "invalid_version",
            "confirm": True,
        },
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should return a numeric error code for invalid version",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADMIN_DB_ACCEPTED_TESTS))
def test_setFeatureCompatibilityVersion_admin_db_accepted(database_client, collection, test):
    """Test setFeatureCompatibilityVersion succeeds on the admin database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True}
    )
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(USER_DB_REJECTED_TESTS))
def test_setFeatureCompatibilityVersion_user_db_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion fails on a user database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = _get_fcv(collection)
    result = execute_command(collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True})
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(UNRECOGNIZED_FIELD_TESTS))
def test_setFeatureCompatibilityVersion_unrecognized_field(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects unrecognized fields."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = _get_fcv(collection)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(SET_PARAMETER_TESTS))
def test_setFeatureCompatibilityVersion_set_parameter_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion cannot be set through setParameter."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(ERROR_CODE_TESTS))
def test_setFeatureCompatibilityVersion_error_code(database_client, collection, test):
    """Test setFeatureCompatibilityVersion error response contains a numeric code."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
