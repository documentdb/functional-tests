"""Tests for autoCompact request validation: type strictness, null, and bad fields."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.system.administration.commands.autoCompact.utils.autoCompact_common import (  # noqa: E501
    ensure_autocompact_idle,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO, INT32_ZERO

# Property [Null Command Value]: a null autoCompact command value is treated as
# a missing required field rather than a wrong type.
AUTOCOMPACT_NULL_COMMAND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_command_value",
        command=lambda ctx: {"autoCompact": None},
        error_code=MISSING_FIELD_ERROR,
        msg="autoCompact should reject a null command value as a missing required field",
    ),
]

# Property [Value Type Strictness]: every non-bool BSON type for the autoCompact
# command value is rejected with a type mismatch error rather than coerced to a
# boolean, and a literal array is rejected without unwrapping.
AUTOCOMPACT_VALUE_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"value_type_{tid}",
            command=lambda ctx, v=val: {"autoCompact": v},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"autoCompact should reject a {tid} command value as the wrong type",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("string", "true"),
            ("object", {"a": 1}),
            ("array", []),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01")),
            ("regex", Regex(".*")),
            ("code", Code("x")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "value_array_single_bool",
        command=lambda ctx: {"autoCompact": [True]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="autoCompact should reject a single-element bool array without unwrapping it",
    ),
]

# Property [freeSpaceTargetMB Type Strictness]: every non-numeric BSON type for
# freeSpaceTargetMB is rejected with a type mismatch error rather than coerced
# to a number, and a literal array is rejected without unwrapping.
AUTOCOMPACT_FSTMB_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"fstmb_type_{tid}",
            command=lambda ctx, v=val: {"autoCompact": True, "freeSpaceTargetMB": v},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"autoCompact should reject a {tid} freeSpaceTargetMB as the wrong type",
        )
        for tid, val in [
            ("string", "20"),
            ("bool", True),
            ("object", {"a": 1}),
            ("array", []),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01")),
            ("regex", Regex(".*")),
            ("code", Code("x")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "fstmb_array_single_int",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": [20]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="autoCompact should reject a single-element int array freeSpaceTargetMB without unwrap",
    ),
]

# Property [runOnce Type Strictness]: every non-bool BSON type for runOnce is
# rejected with a type mismatch error rather than coerced to a boolean, so
# numeric 0 and 1 are not accepted.
AUTOCOMPACT_RUNONCE_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"runonce_type_{tid}",
            command=lambda ctx, v=val: {"autoCompact": True, "runOnce": v},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"autoCompact should reject a {tid} runOnce as the wrong type",
        )
        for tid, val in [
            ("string", "true"),
            ("int32_zero", INT32_ZERO),
            ("int32_one", 1),
            ("int64", Int64(1)),
            ("double_zero", DOUBLE_ZERO),
            ("double_one", 1.0),
            ("decimal128", Decimal128("1")),
            ("object", {"$exists": True}),
            ("array", []),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01")),
            ("regex", Regex(".*")),
            ("code", Code("x")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "runonce_array_single_bool",
        command=lambda ctx: {"autoCompact": True, "runOnce": [True]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="autoCompact should reject a single-element bool array runOnce without unwrapping it",
    ),
]

# Property [Unknown Field Handling]: an unknown top-level field is rejected with
# an unknown-field error, and known option names are case-sensitive so wrong-case
# variants are treated as unknown fields and rejected the same way.
AUTOCOMPACT_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field",
        command=lambda ctx: {"autoCompact": True, "bogusField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="autoCompact should reject an unknown top-level field",
    ),
    CommandTestCase(
        "unknown_field_fstmb_capitalized",
        command=lambda ctx: {"autoCompact": True, "FreeSpaceTargetMB": 20},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="autoCompact should treat a wrong-case variant of a known option as an unknown field",
    ),
]

# Property [Generic Envelope Field Rejection]: a writeConcern envelope field is
# rejected with an unsupported-options error on both the enable and disable
# paths.
AUTOCOMPACT_WRITE_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "write_concern_enable",
        command=lambda ctx: {"autoCompact": True, "writeConcern": {"w": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="autoCompact enable should reject writeConcern as an unsupported envelope field",
    ),
    CommandTestCase(
        "write_concern_disable",
        command=lambda ctx: {"autoCompact": False, "writeConcern": {"w": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="autoCompact disable should reject writeConcern as an unsupported envelope field",
    ),
]

AUTOCOMPACT_REQUEST_VALIDATION_TESTS: list[CommandTestCase] = (
    AUTOCOMPACT_NULL_COMMAND_TESTS
    + AUTOCOMPACT_VALUE_TYPE_STRICTNESS_TESTS
    + AUTOCOMPACT_FSTMB_TYPE_STRICTNESS_TESTS
    + AUTOCOMPACT_RUNONCE_TYPE_STRICTNESS_TESTS
    + AUTOCOMPACT_UNKNOWN_FIELD_TESTS
    + AUTOCOMPACT_WRITE_CONCERN_TESTS
)


@pytest.mark.no_parallel
@pytest.mark.parametrize("test", pytest_params(AUTOCOMPACT_REQUEST_VALIDATION_TESTS))
def test_autoCompact_request_validation(database_client, collection, test):
    """Test autoCompact rejection of malformed requests (type, null, bad fields)."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    # Ensure autoCompact is idle first: a leftover config from a prior test
    # would otherwise conflict.
    ensure_autocompact_idle(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
