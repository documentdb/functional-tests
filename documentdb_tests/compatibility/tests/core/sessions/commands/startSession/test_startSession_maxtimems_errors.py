"""Tests for startSession maxTimeMS error cases."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [maxTimeMS Type Rejection]: non-numeric maxTimeMS values produce a type error.
STARTSESSION_MAXTIMEMS_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_type_reject_{tid}",
        command=lambda ctx, v=val: {"startSession": 1, "maxTimeMS": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"startSession should reject {tid} maxTimeMS with type mismatch error",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("string", "1000"),
        ("object", {}),
        ("array", []),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [maxTimeMS Negative Rejection]: negative maxTimeMS values are rejected.
STARTSESSION_MAXTIMEMS_NEGATIVE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_negative_{tid}",
        command=lambda ctx, v=val: {"startSession": 1, "maxTimeMS": v},
        error_code=BAD_VALUE_ERROR,
        msg=f"startSession should reject negative {tid} maxTimeMS",
    )
    for tid, val in [
        ("int32", -1),
        ("int64", Int64(-1)),
        ("double", -1.0),
        ("decimal128", Decimal128("-1")),
    ]
]

# Property [maxTimeMS Overflow Rejection]: maxTimeMS values exceeding INT32_MAX are rejected.
STARTSESSION_MAXTIMEMS_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxtimems_overflow_int32_max_plus_1",
        command=lambda ctx: {"startSession": 1, "maxTimeMS": Int64(2_147_483_648)},
        error_code=BAD_VALUE_ERROR,
        msg="startSession should reject maxTimeMS exceeding INT32_MAX",
    ),
    CommandTestCase(
        "maxtimems_overflow_int64_max",
        command=lambda ctx: {"startSession": 1, "maxTimeMS": Int64(9_223_372_036_854_775_807)},
        error_code=BAD_VALUE_ERROR,
        msg="startSession should reject INT64_MAX maxTimeMS",
    ),
]

# Property [maxTimeMS Fractional Rejection]: fractional maxTimeMS values are rejected.
STARTSESSION_MAXTIMEMS_FRACTIONAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxtimems_fractional_half",
        command=lambda ctx: {"startSession": 1, "maxTimeMS": 0.5},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="startSession should reject fractional maxTimeMS 0.5",
    ),
    CommandTestCase(
        "maxtimems_fractional_100_5",
        command=lambda ctx: {"startSession": 1, "maxTimeMS": 100.5},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="startSession should reject fractional maxTimeMS 100.5",
    ),
]

STARTSESSION_MAXTIMEMS_ERROR_TESTS = (
    STARTSESSION_MAXTIMEMS_TYPE_REJECTION_TESTS
    + STARTSESSION_MAXTIMEMS_NEGATIVE_TESTS
    + STARTSESSION_MAXTIMEMS_OVERFLOW_TESTS
    + STARTSESSION_MAXTIMEMS_FRACTIONAL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_MAXTIMEMS_ERROR_TESTS))
def test_startSession_maxtimems_errors(database_client, collection, test):
    """Test startSession maxTimeMS error cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
