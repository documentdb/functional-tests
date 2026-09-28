"""Tests for setFeatureCompatibilityVersion error cases.

Covers database enforcement (user/local/config DB rejection), unknown/extra fields,
error response structure, and setParameter rejection.
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

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


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
    CommandTestCase(
        "writeConcern_unknown_subfield",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setFeatureCompatibilityVersion should reject unknown sub-fields in writeConcern",
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


# Property [Error Contains Code]: invalid version returns FCV_INVALID_VERSION_ERROR.
ERROR_CODE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "invalid_version_returns_error",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "invalid_version",
            "confirm": True,
        },
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should return FCV_INVALID_VERSION_ERROR"
        " for non-existent version string",
    ),
]


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


@pytest.mark.parametrize("test", pytest_params(ERROR_CODE_TESTS))
def test_setFeatureCompatibilityVersion_invalid_version_error(database_client, collection, test):
    """Test setFeatureCompatibilityVersion returns FCV_INVALID_VERSION_ERROR."""
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
