"""Tests for setParameter argument validation (success cases).

Validates control field type acceptance, parameter name acceptance,
and parameter value type coercion behavior.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Control Field Type]: setParameter control field accepts various BSON types.
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
    assertSuccessPartial(
        result, {"ok": 1.0}, msg=f"setParameter control field should accept {desc}"
    )


# Property [Name Acceptance]: setParameter accepts known runtime parameter names.
NAME_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "known_param",
        command=lambda ctx: {"setParameter": 1, "logLevel": 0},
        expected={"ok": 1.0},
        msg="setParameter should accept known runtime param",
    ),
    CommandTestCase(
        "control_field_int64_max",
        command=lambda ctx: {"setParameter": Int64(9_223_372_036_854_775_807), "logLevel": 0},
        expected={"ok": 1.0},
        msg="setParameter should accept Int64 max as control field value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAME_ACCEPTANCE_TESTS))
def test_setParameter_name_accepted(database_client, collection, test):
    """Test setParameter accepts valid parameter names."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


# Standalone tests below require save/restore of server state after each set.


# Property [Boolean Coercion]: boolean-typed parameters accept bool and numeric coercion.
def test_setParameter_boolean_param_with_bool_succeeds(collection):
    """Test setParameter accepts boolean value for boolean-typed param."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": True})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setParameter should accept bool for boolean param"
    )
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


def test_setParameter_boolean_param_with_int_coerces(collection):
    """Test setParameter coerces integer to boolean for boolean-typed param."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="setParameter should coerce int to bool")
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


# Property [Integer Coercion]: integer-typed parameters accept numeric coercion.
def test_setParameter_integer_param_with_int_succeeds(collection):
    """Test setParameter accepts integer for integer-typed param."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setParameter should accept int for integer param"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_integer_param_with_whole_double_succeeds(collection):
    """Test setParameter accepts whole-number double for integer-typed param."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1.0})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setParameter should accept whole double for integer param"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_integer_param_with_fractional_double_coerces(collection):
    """Test setParameter truncates fractional double for integer-typed param."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 1.5})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setParameter should truncate fractional double for integer param"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


def test_setParameter_integer_param_valid_range(collection):
    """Test setParameter accepts integer at valid upper bound."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": 5})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setParameter should accept logLevel at upper bound"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


# Property [String Param Acceptance]: string-typed parameters accept valid strings.
def test_setParameter_string_param_valid_succeeds(collection):
    """Test setParameter accepts valid short string for string-typed param."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "automationServiceDescriptor": "test"}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="setParameter should accept valid string value")
    execute_admin_command(collection, {"setParameter": 1, "automationServiceDescriptor": ""})
