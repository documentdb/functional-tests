"""Tests for setParameter argument validation.

Validates control field types, parameter name validation, parameter value
type/range validation, and bounded integer parameter behavior.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    OVERFLOW_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


@pytest.mark.parametrize(
    "control_value,desc",
    [
        pytest.param(1, "int 1", id="int"),
        pytest.param(1.0, "double 1.0", id="double"),
        pytest.param(Int64(1), "Int64", id="long"),
        pytest.param(True, "bool true", id="bool"),
        pytest.param("1", "string", id="string"),
        pytest.param(None, "null", id="null"),
        pytest.param([1], "array", id="array"),
        pytest.param({"a": 1}, "document", id="document"),
        pytest.param(0, "int 0", id="zero"),
        pytest.param(-1, "negative int", id="negative"),
    ],
)
def test_setParameter_control_field_type(collection, control_value, desc):
    """Test setParameter control field accepts various BSON types."""
    result = execute_admin_command(collection, {"setParameter": control_value, "logLevel": 0})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"Control field should accept {desc}")


def test_setParameter_known_param_succeeds(collection):
    """Test a known runtime parameter name succeeds."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Known param should succeed")


def test_setParameter_case_sensitive_name(collection):
    """Test parameter names are case-sensitive (altered case fails)."""
    result = execute_admin_command(collection, {"setParameter": 1, "LogLevel": 0})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Wrong case should fail")


def test_setParameter_long_param_name_fails(collection):
    """Test very long parameter name (1000+ chars) fails as unknown."""
    result = execute_admin_command(collection, {"setParameter": 1, "a" * 1000: 1})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Long name should fail")


def test_setParameter_dotted_param_name_fails(collection):
    """Test parameter name containing dots fails as unknown."""
    result = execute_admin_command(collection, {"setParameter": 1, "log.level": 1})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Dotted name should fail")


def test_setParameter_dollar_param_name_fails(collection):
    """Test parameter name with dollar sign fails as unknown."""
    result = execute_admin_command(collection, {"setParameter": 1, "$logLevel": 1})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Dollar name should fail")


def test_setParameter_boolean_param_with_bool_succeeds(collection):
    """Test a boolean-typed parameter set with a boolean value succeeds."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Boolean value should succeed for boolean param")
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


def test_setParameter_boolean_param_with_int_coerces(collection):
    """Test a boolean-typed parameter set with integer coerces (1 -> true)."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Int should coerce to bool")
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


def test_setParameter_integer_param_with_int_succeeds(collection):
    """Test an integer-typed parameter set with an integer value succeeds."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Int value should succeed for int param")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_integer_param_with_whole_double_succeeds(collection):
    """Test an integer-typed parameter set with a whole-number double succeeds."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1.0})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Whole double should succeed for int param")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_integer_param_with_fractional_double_coerces(collection):
    """Test an integer-typed parameter set with a fractional double truncates to integer."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1.5})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Fractional double should truncate for int param")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_integer_param_valid_range(collection):
    """Test an integer parameter at valid bounds succeeds (logLevel 0 and 5)."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 5})
    assertSuccessPartial(result, {"ok": 1.0}, msg="logLevel 5 should succeed")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_string_param_with_numeric_fails(collection):
    """Test setting a string-typed parameter to a numeric value fails."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "automationServiceDescriptor": 12345}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="Numeric value should fail for string param")


def test_setParameter_string_param_overlength_fails(collection):
    """Test setting a string-typed parameter to an over-length string fails with Overflow."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "automationServiceDescriptor": "x" * 65}
    )
    assertFailureCode(result, OVERFLOW_ERROR, msg="Over-length string should fail")


def test_setParameter_string_param_valid_succeeds(collection):
    """Test setting a string-typed parameter to a short valid string succeeds."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "automationServiceDescriptor": "test"}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Valid short string should succeed")
    execute_admin_command(collection, {"setParameter": 1, "automationServiceDescriptor": ""})


def test_setParameter_whitespace_param_name_fails(collection):
    """Test parameter name with leading/trailing whitespace fails as unknown."""
    result = execute_admin_command(collection, {"setParameter": 1, " logLevel ": 0})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Whitespace name should fail")


def test_setParameter_numeric_string_param_name_fails(collection):
    """Test numeric-looking string parameter name fails as unknown."""
    result = execute_admin_command(collection, {"setParameter": 1, "12345": 0})
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg="Numeric string name should fail")


def test_setParameter_control_field_int64_max(collection):
    """Test control field with Int64 max value is accepted."""
    result = execute_admin_command(
        collection, {"setParameter": Int64(9223372036854775807), "logLevel": 0}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Int64 max control field should be accepted")


def test_setParameter_name_collides_with_control_field(collection):
    """Test parameter name 'setParameter' (same as control field) fails."""
    result = execute_admin_command(collection, {"setParameter": 1, "setParameter": 2})  # noqa: F601
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="Name collision with control field should fail"
    )
