"""Tests for setFeatureCompatibilityVersion error cases.

Covers admin-database-only enforcement, unknown/extra fields,
response structure, and setParameter rejection.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    FCV_INVALID_VERSION_ERROR,
    ILLEGAL_OPERATION_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


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


# Property [System DB Rejected]: setFeatureCompatibilityVersion fails on local and config databases.
SYSTEM_DB_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "local_db_rejected",
        error_code=UNAUTHORIZED_ERROR,
        msg="setFeatureCompatibilityVersion should reject execution on the local database",
    ),
    CommandTestCase(
        "config_db_rejected",
        error_code=UNAUTHORIZED_ERROR,
        msg="setFeatureCompatibilityVersion should reject execution on the config database",
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


# Property [writeConcern Unknown Sub-field]: unknown fields inside writeConcern are rejected.
WRITE_CONCERN_UNKNOWN_SUBFIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeConcern_unknown_subfield",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setFeatureCompatibilityVersion should reject unknown sub-fields inside writeConcern",
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


# Property [Success Response Structure]: success response contains ok:1.
SUCCESS_RESPONSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "success_contains_ok",
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion success response should contain ok:1",
    ),
]


# Property [Error Response Structure]: error response contains code and codeName.
ERROR_RESPONSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "error_contains_code_and_codeName",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "invalid_version",
            "confirm": True,
        },
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion error response should contain code and codeName",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADMIN_DB_ACCEPTED_TESTS))
def test_setFeatureCompatibilityVersion_admin_db_accepted(database_client, collection, test):
    """Test setFeatureCompatibilityVersion succeeds on the admin database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
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
    fcv = get_fcv(collection)
    result = execute_command(collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True})
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(SYSTEM_DB_REJECTED_TESTS))
def test_setFeatureCompatibilityVersion_system_db_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion fails on local and config databases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
    db_name = "local" if "local" in test.id else "config"
    target_collection = collection.database.client[db_name]["test"]
    result = execute_command(
        target_collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True}
    )
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
    cmd["setFeatureCompatibilityVersion"] = get_fcv(collection)
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


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_UNKNOWN_SUBFIELD_TESTS))
def test_setFeatureCompatibilityVersion_writeConcern_unknown_subfield(
    database_client, collection, test
):
    """Test setFeatureCompatibilityVersion rejects unknown sub-fields inside writeConcern."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = get_fcv(collection)
    result = execute_admin_command(collection, cmd)
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


@pytest.mark.parametrize("test", pytest_params(SUCCESS_RESPONSE_TESTS))
def test_setFeatureCompatibilityVersion_success_response(database_client, collection, test):
    """Test setFeatureCompatibilityVersion success response contains ok:1."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
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


@pytest.mark.parametrize("test", pytest_params(ERROR_RESPONSE_TESTS))
def test_setFeatureCompatibilityVersion_error_response(database_client, collection, test):
    """Test setFeatureCompatibilityVersion error response contains code and codeName."""
    collection = test.prepare(database_client, collection)
    result = execute_admin_command(
        collection, test.build_command(CommandContext.from_collection(collection))
    )
    assertFailureCode(result, test.error_code, msg=test.msg)
