"""Tests for killAllSessions maxTimeMS field rejection."""

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
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_OVERFLOW,
)

pytestmark = pytest.mark.no_parallel

# Property [maxTimeMS Type Rejection]: non-numeric maxTimeMS values are rejected.
KILLALLSESSIONS_MAXTIMEMS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_type_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "maxTimeMS": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killAllSessions should reject {tid} for maxTimeMS",
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

# Property [maxTimeMS Value Rejection — Fractional]: fractional maxTimeMS values are rejected.
KILLALLSESSIONS_MAXTIMEMS_FRACTIONAL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_fractional_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "maxTimeMS": v},
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"killAllSessions should reject fractional {tid} maxTimeMS",
    )
    for tid, val in [
        ("double_half", 0.5),
        ("double_one_and_half", 100.5),
        ("decimal128_one_and_half", DECIMAL128_ONE_AND_HALF),
    ]
]

# Property [maxTimeMS Value Rejection — NaN/Infinity]: NaN and Infinity values are rejected.
KILLALLSESSIONS_MAXTIMEMS_NAN_INF_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_value_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "maxTimeMS": v},
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"killAllSessions should reject {tid} maxTimeMS",
    )
    for tid, val in [
        ("double_nan", FLOAT_NAN),
        ("double_negative_nan", FLOAT_NEGATIVE_NAN),
        ("double_positive_infinity", FLOAT_INFINITY),
        ("double_negative_infinity", FLOAT_NEGATIVE_INFINITY),
        ("decimal128_nan", DECIMAL128_NAN),
        ("decimal128_negative_nan", DECIMAL128_NEGATIVE_NAN),
        ("decimal128_positive_infinity", DECIMAL128_INFINITY),
        ("decimal128_negative_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [maxTimeMS Range Rejection]: negative values and values exceeding
# the size limit are rejected.
KILLALLSESSIONS_MAXTIMEMS_RANGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_range_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "maxTimeMS": v},
        error_code=BAD_VALUE_ERROR,
        msg=f"killAllSessions should reject {tid} maxTimeMS",
    )
    for tid, val in [
        ("int32_negative", -1),
        ("int64_negative", Int64(-1)),
        ("double_negative", -1.0),
        ("decimal128_negative", Decimal128("-1")),
        ("int64_overflow", Int64(INT32_OVERFLOW)),
        ("int64_max_overflow", Int64(9223372036854775807)),
    ]
]

KILLALLSESSIONS_MAXTIMEMS_ERROR_TESTS: list[CommandTestCase] = (
    KILLALLSESSIONS_MAXTIMEMS_TYPE_ERROR_TESTS
    + KILLALLSESSIONS_MAXTIMEMS_FRACTIONAL_ERROR_TESTS
    + KILLALLSESSIONS_MAXTIMEMS_NAN_INF_ERROR_TESTS
    + KILLALLSESSIONS_MAXTIMEMS_RANGE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_MAXTIMEMS_ERROR_TESTS))
def test_killAllSessions_maxtimems_errors(collection, test):
    """Test killAllSessions maxTimeMS field rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
