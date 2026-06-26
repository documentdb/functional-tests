"""Tests for setParameter error codes and multi-parameter failure semantics.

Validates correct error codes are returned for various failure modes and
that multi-parameter commands behave atomically on failure.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Error Codes]: setParameter returns correct error codes for invalid inputs.
ERROR_CODE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "nonexistent_param",
        command=lambda ctx: {"setParameter": 1, "nonExistentXYZ": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject non-existent param",
    ),
    CommandTestCase(
        "startup_only_param",
        command=lambda ctx: {"setParameter": 1, "port": 27018},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject startup-only param",
    ),
    CommandTestCase(
        "out_of_range_value",
        command=lambda ctx: {"setParameter": 1, "logLevel": -1},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject out-of-range value below minimum",
    ),
    CommandTestCase(
        "above_max_value",
        command=lambda ctx: {"setParameter": 1, "logLevel": INT32_MAX + 1},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject value exceeding int32 max",
    ),
    CommandTestCase(
        "wrong_type_value",
        command=lambda ctx: {"setParameter": 1, "logLevel": "abc"},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject wrong type value",
    ),
    CommandTestCase(
        "empty_param_name",
        command=lambda ctx: {"setParameter": 1, "": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject empty param name",
    ),
    CommandTestCase(
        "no_param_pair",
        command=lambda ctx: {"setParameter": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject missing param pair",
    ),
    CommandTestCase(
        "multi_param_with_invalid",
        command=lambda ctx: {"setParameter": 1, "logLevel": 0, "nonExistentXYZ": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject multi-param command when one is invalid",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_CODE_TESTS))
def test_setParameter_errors(database_client, collection, test):
    """Test setParameter error cases."""
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


# Property [Non-Admin Rejection]: setParameter fails on non-admin database.
NON_ADMIN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_admin_db",
        command=lambda ctx: {"setParameter": 1, "logLevel": 0},
        error_code=UNAUTHORIZED_ERROR,
        msg="setParameter should reject non-admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_ADMIN_TESTS))
def test_setParameter_non_admin_db(database_client, collection, test):
    """Test setParameter fails on non-admin database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Atomicity]: multi-parameter set is atomic on failure.
# Standalone because it requires multi-step state verification.
def test_setParameter_multi_param_atomic_on_failure(collection):
    """Test multi-parameter command with invalid second param does not apply first."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 3, "nonExistentXYZ": 1})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"logLevel": 0}, msg="First param should not be applied when second fails"
    )
