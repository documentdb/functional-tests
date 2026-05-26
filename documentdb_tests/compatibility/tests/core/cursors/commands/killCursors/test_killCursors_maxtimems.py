"""Tests for killCursors maxTimeMS field."""

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_ZERO,
)

# Property [maxTimeMS Acceptance]: maxTimeMS accepts values at both
# boundaries of the valid range across all numeric types.
KILLCURSORS_MAXTIMEMS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "maxTimeMS": v,
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg=f"killCursors should accept {tid} maxTimeMS",
    )
    for tid, val in [
        # Lower boundary (0) in all representations.
        ("int32_zero", 0),
        ("int64_zero", INT64_ZERO),
        ("double_zero", DOUBLE_ZERO),
        ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("decimal128_negative_zero", DECIMAL128_NEGATIVE_ZERO),
        # Upper boundary (INT32_MAX) in all representations.
        ("int32_max", INT32_MAX),
        ("int64_max", Int64(INT32_MAX)),
        ("double_max", float(INT32_MAX)),
        ("decimal128_max", Decimal128(str(INT32_MAX))),
    ]
]

# Property [maxTimeMS Type Rejection]: all non-numeric, non-null BSON
# types for maxTimeMS are rejected.
KILLCURSORS_MAXTIMEMS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_type_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "maxTimeMS": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killCursors should reject {tid} for maxTimeMS",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("string", "100"),
        ("object", {"a": 1}),
        ("array", [1, 2]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("binary", Binary(b"\x01")),
        ("binary_uuid", Binary(b"\x00" * 16, subtype=4)),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [maxTimeMS Value Rejection]: values outside the valid range
# or not representable as whole integers are rejected.
KILLCURSORS_MAXTIMEMS_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_value_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "maxTimeMS": v,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"killCursors should reject {tid} maxTimeMS",
    )
    for tid, val in [
        # Fractional values.
        ("fractional_double", 1.5),
        ("fractional_decimal128", DECIMAL128_ONE_AND_HALF),
        # Double NaN and Infinity.
        ("double_nan", FLOAT_NAN),
        ("double_negative_nan", FLOAT_NEGATIVE_NAN),
        ("double_positive_infinity", FLOAT_INFINITY),
        ("double_negative_infinity", FLOAT_NEGATIVE_INFINITY),
        # Decimal128 NaN and Infinity.
        ("decimal128_nan", DECIMAL128_NAN),
        ("decimal128_negative_nan", DECIMAL128_NEGATIVE_NAN),
        ("decimal128_positive_infinity", DECIMAL128_INFINITY),
        ("decimal128_negative_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
] + [
    CommandTestCase(
        f"maxtimems_value_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1)],
            "maxTimeMS": v,
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"killCursors should reject {tid} maxTimeMS",
    )
    for tid, val in [
        # Below lower boundary.
        ("int32_negative", -1),
        ("int64_negative", Int64(-1)),
        ("double_negative", -1.0),
        ("decimal128_negative", Decimal128("-1")),
        # Above upper boundary.
        ("int32_overflow", INT32_OVERFLOW),
        ("int64_overflow", Int64(INT32_OVERFLOW)),
        ("double_overflow", float(INT32_OVERFLOW)),
        ("decimal128_overflow", Decimal128(str(INT32_OVERFLOW))),
    ]
]

KILLCURSORS_MAXTIMEMS_TESTS: list[CommandTestCase] = (
    KILLCURSORS_MAXTIMEMS_ACCEPTANCE_TESTS
    + KILLCURSORS_MAXTIMEMS_TYPE_ERROR_TESTS
    + KILLCURSORS_MAXTIMEMS_VALUE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_MAXTIMEMS_TESTS))
def test_killCursors_maxtimems(collection, test):
    """Test killCursors maxTimeMS field."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
