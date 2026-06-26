"""Tests for setParameter error codes and multi-parameter failure semantics.

Validates correct error codes are returned for various failure modes and
that multi-parameter commands behave atomically on failure.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_setParameter_nonexistent_param_error_code(collection):
    """Test setting a non-existent parameter returns InvalidOptions."""
    result = execute_admin_command(collection, {"setParameter": 1, "nonExistentXYZ": 1})
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="setParameter should reject non-existent param"
    )


def test_setParameter_startup_only_param_error_code(collection):
    """Test setting a startup-only parameter at runtime returns InvalidOptions."""
    result = execute_admin_command(collection, {"setParameter": 1, "port": 27018})
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="setParameter should reject startup-only param"
    )


def test_setParameter_out_of_range_error_code(collection):
    """Test setting a parameter to an out-of-range value returns BadValue."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": -1})
    assertFailureCode(result, BAD_VALUE_ERROR, msg="setParameter should reject out-of-range value")


def test_setParameter_wrong_type_error_code(collection):
    """Test setting a parameter to a wrong-type value returns BadValue."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": "abc"})
    assertFailureCode(result, BAD_VALUE_ERROR, msg="setParameter should reject wrong type value")


def test_setParameter_non_admin_db_error_code(collection):
    """Test running setParameter on a non-admin database returns Unauthorized."""
    result = execute_command(collection, {"setParameter": 1, "logLevel": 0})
    assertFailureCode(
        result, UNAUTHORIZED_ERROR, msg="setParameter should reject non-admin database"
    )


def test_setParameter_empty_name_error_code(collection):
    """Test empty-string parameter name returns InvalidOptions."""
    result = execute_admin_command(collection, {"setParameter": 1, "": 1})
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="setParameter should reject empty param name"
    )


def test_setParameter_no_param_pair_fails(collection):
    """Test setParameter with control field but no parameter:value pair fails."""
    result = execute_admin_command(collection, {"setParameter": 1})
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="setParameter should reject missing param pair"
    )


def test_setParameter_multi_param_second_invalid_is_atomic(collection):
    """Test multi-parameter command with invalid second param does not apply first."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 3, "nonExistentXYZ": 1})
    result = execute_admin_command(collection, {"getParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"logLevel": 0}, msg="First param should not be applied when second fails"
    )


def test_setParameter_multi_param_invalid_returns_error(collection):
    """Test multi-parameter command with invalid param returns error code."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "logLevel": 0, "nonExistentXYZ": 1}
    )
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="Multi-param with invalid should return 72"
    )
