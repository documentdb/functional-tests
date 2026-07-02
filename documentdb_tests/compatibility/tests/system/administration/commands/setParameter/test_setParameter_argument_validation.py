"""Tests for setParameter argument validation (success cases).

Validates control field Int64 max, parameter value range, and string param acceptance.
Type coercion matrices are in test_setParameter_bson_type_validation.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_MAX

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Name Acceptance]: setParameter accepts edge-case control field values.
NAME_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "control_field_int64_max",
        command=lambda ctx: {"setParameter": INT64_MAX, "logLevel": 0},
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


# Property [Integer Range]: integer-typed parameters accept values within valid bounds.
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
