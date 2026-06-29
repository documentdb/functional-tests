"""Tests for setUserWriteBlockMode argument validation errors.

Validates type rejection for the global and reason fields, missing required fields,
invalid enum values, and unrecognized fields.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.administration.commands.setUserWriteBlockMode.utils.write_block_helpers import (  # noqa: E501
    force_disable_write_block,
)
from documentdb_tests.compatibility.tests.system.administration.commands.utils.admin_test_case import (  # noqa: E501
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, FLOAT_NAN

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


@pytest.fixture(autouse=True)
def _manage_write_block(collection):
    """Ensure write block is disabled before and after each test."""
    force_disable_write_block(collection)
    yield
    force_disable_write_block(collection)


# Property [Global Field Type Rejection]: setUserWriteBlockMode rejects all non-boolean types
# for the global field with no coercion.
GLOBAL_TYPE_REJECTION_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        f"global_type_{tid}",
        command=lambda ctx, v=val: {"setUserWriteBlockMode": 1, "global": v},
        error_code=error,
        msg=f"setUserWriteBlockMode should reject {tid} for global field",
    )
    for tid, val, error in [
        ("int32_1", 1, TYPE_MISMATCH_ERROR),
        ("int32_0", 0, TYPE_MISMATCH_ERROR),
        ("double_1", 1.0, TYPE_MISMATCH_ERROR),
        ("double_0", 0.0, TYPE_MISMATCH_ERROR),
        ("int64", Int64(1), TYPE_MISMATCH_ERROR),
        ("decimal128", Decimal128("1"), TYPE_MISMATCH_ERROR),
        ("nan", FLOAT_NAN, TYPE_MISMATCH_ERROR),
        ("infinity", FLOAT_INFINITY, TYPE_MISMATCH_ERROR),
        ("negative_infinity", float("-inf"), TYPE_MISMATCH_ERROR),
        ("negative_zero", -0.0, TYPE_MISMATCH_ERROR),
        ("string", "true", TYPE_MISMATCH_ERROR),
        ("array", [], TYPE_MISMATCH_ERROR),
        ("object", {}, TYPE_MISMATCH_ERROR),
        ("null", None, MISSING_FIELD_ERROR),
    ]
]

# Property [Missing Global Field]: setUserWriteBlockMode requires the global field.
MISSING_GLOBAL_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "missing_global",
        command=lambda ctx: {"setUserWriteBlockMode": 1},
        error_code=MISSING_FIELD_ERROR,
        msg="setUserWriteBlockMode should require the global field",
    ),
]

# Property [Reason Field Type Rejection]: setUserWriteBlockMode rejects non-string types for
# the reason field.
REASON_TYPE_REJECTION_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        f"reason_type_{tid}",
        command=lambda ctx, v=val: {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setUserWriteBlockMode should reject {tid} for reason field",
    )
    for tid, val in [
        ("int", 1),
        ("bool", True),
        ("array", []),
        ("object", {}),
    ]
]

# Property [Reason Field Invalid Enum]: setUserWriteBlockMode rejects unrecognized reason
# strings.
REASON_INVALID_ENUM_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "reason_invalid_enum",
        command=lambda ctx: {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": "InvalidReason",
        },
        error_code=BAD_VALUE_ERROR,
        msg="setUserWriteBlockMode should reject unrecognized reason enum value",
    ),
]

# Property [Unrecognized Fields]: setUserWriteBlockMode rejects unknown fields.
UNRECOGNIZED_FIELD_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "unrecognized_field",
        command=lambda ctx: {
            "setUserWriteBlockMode": 1,
            "global": False,
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setUserWriteBlockMode should reject unrecognized fields",
    ),
]

ARGUMENT_ERROR_TESTS: list[AdminTestCase] = (
    GLOBAL_TYPE_REJECTION_TESTS
    + MISSING_GLOBAL_TESTS
    + REASON_TYPE_REJECTION_TESTS
    + REASON_INVALID_ENUM_TESTS
    + UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_ERROR_TESTS))
def test_setUserWriteBlockMode_argument_error(collection, test):
    """Test setUserWriteBlockMode rejects invalid arguments."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertFailureCode(result, test.error_code, msg=test.msg)
