"""Tests for setParameter error cases.

ALL error assertions for setParameter are consolidated in this file.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    OVERFLOW_ERROR,
    TYPE_MISMATCH_ERROR,
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
        "out_of_range_below_min",
        command=lambda ctx: {"setParameter": 1, "logLevel": -1},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject value below minimum",
    ),
    CommandTestCase(
        "above_int32_max",
        command=lambda ctx: {"setParameter": 1, "logLevel": INT32_MAX + 1},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject value exceeding int32 max",
    ),
    CommandTestCase(
        "wrong_type_string_for_int",
        command=lambda ctx: {"setParameter": 1, "logLevel": "abc"},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject string for integer param",
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

# Property [Name Rejection]: setParameter rejects invalid parameter names.
NAME_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "case_sensitive",
        command=lambda ctx: {"setParameter": 1, "LogLevel": 0},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject wrong-case param name",
    ),
    CommandTestCase(
        "long_name",
        command=lambda ctx: {"setParameter": 1, "a" * 1000: 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject very long param name",
    ),
    CommandTestCase(
        "dotted_name",
        command=lambda ctx: {"setParameter": 1, "log.level": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject dotted param name",
    ),
    CommandTestCase(
        "dollar_name",
        command=lambda ctx: {"setParameter": 1, "$logLevel": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject dollar-prefixed param name",
    ),
    CommandTestCase(
        "whitespace_name",
        command=lambda ctx: {"setParameter": 1, " logLevel ": 0},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject whitespace in param name",
    ),
    CommandTestCase(
        "numeric_string_name",
        command=lambda ctx: {"setParameter": 1, "12345": 0},
        error_code=INVALID_OPTIONS_ERROR,
        msg="setParameter should reject numeric string param name",
    ),
]

# Property [Value Type Rejection]: setParameter rejects invalid value types.
VALUE_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string_param_with_numeric",
        command=lambda ctx: {"setParameter": 1, "automationServiceDescriptor": 12345},
        error_code=TYPE_MISMATCH_ERROR,
        msg="setParameter should reject numeric value for string param",
    ),
    CommandTestCase(
        "string_param_overlength",
        command=lambda ctx: {"setParameter": 1, "automationServiceDescriptor": "x" * 65},
        error_code=OVERFLOW_ERROR,
        msg="setParameter should reject over-length string value",
    ),
]

# Property [Hierarchical Type Rejection]: logComponentVerbosity rejects invalid types.
HIERARCHICAL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hierarchical_string_value",
        command=lambda ctx: {"setParameter": 1, "logComponentVerbosity": "abc"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="setParameter should reject string for logComponentVerbosity",
    ),
    CommandTestCase(
        "hierarchical_nested_string_verbosity",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": "abc"}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject string for nested verbosity",
    ),
    CommandTestCase(
        "hierarchical_nested_overflow",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": INT32_MAX + 1}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject overflow for nested verbosity",
    ),
    CommandTestCase(
        "hierarchical_nested_underflow",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": -2_147_483_649}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject underflow for nested verbosity",
    ),
    CommandTestCase(
        "hierarchical_unknown_component",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"unknownComponent": {"verbosity": 1}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject unknown component name",
    ),
    CommandTestCase(
        "hierarchical_nested_nan_verbosity",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": float("nan")}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject NaN for nested verbosity",
    ),
]

# Property [Integer Coercion Rejected]: integer-typed params reject non-numeric types.
INTEGER_COERCION_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "integer_rejects_string",
        command=lambda ctx: {"setParameter": 1, "logLevel": "1"},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject string for integer param",
    ),
    CommandTestCase(
        "integer_rejects_array",
        command=lambda ctx: {"setParameter": 1, "logLevel": [1]},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject array for integer param",
    ),
    CommandTestCase(
        "integer_rejects_document",
        command=lambda ctx: {"setParameter": 1, "logLevel": {"a": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject document for integer param",
    ),
]

ALL_ERROR_TESTS = (
    ERROR_CODE_TESTS
    + NAME_REJECTION_TESTS
    + VALUE_TYPE_REJECTION_TESTS
    + HIERARCHICAL_ERROR_TESTS
    + INTEGER_COERCION_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
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


# Property [Name Collision]: parameter name matching control field name fails.
def test_setParameter_name_collides_with_control_field(collection):
    """Test setParameter rejects param name that collides with control field."""
    result = execute_admin_command(collection, {"setParameter": 1, "setParameter": 2})  # noqa: F601
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="setParameter should reject name collision"
    )
