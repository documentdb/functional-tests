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


# Property [Argument Validation]: setParameter accepts valid argument variations.
ARGUMENT_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "control_field_int64_max",
        command=lambda ctx: {"setParameter": INT64_MAX, "logLevel": 0},
        expected={"ok": 1.0},
        msg="setParameter should accept Int64 max as control field value",
    ),
    CommandTestCase(
        "fractional_double_coerces",
        command=lambda ctx: {"setParameter": 1, "logLevel": 1.5},
        expected={"ok": 1.0},
        msg="setParameter should truncate fractional double for integer param",
    ),
    CommandTestCase(
        "integer_valid_range",
        command=lambda ctx: {"setParameter": 1, "logLevel": 5},
        expected={"ok": 1.0},
        msg="setParameter should accept logLevel at upper bound",
    ),
    CommandTestCase(
        "string_param_valid",
        command=lambda ctx: {"setParameter": 1, "automationServiceDescriptor": "test"},
        expected={"ok": 1.0},
        msg="setParameter should accept valid string value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_VALIDATION_TESTS))
def test_setParameter_argument_validation(database_client, collection, test):
    """Test setParameter argument validation cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
