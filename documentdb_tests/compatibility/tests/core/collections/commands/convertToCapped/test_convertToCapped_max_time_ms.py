"""Tests for convertToCapped command - maxTimeMS parameter validation."""

import datetime

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
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
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
)

# Property [maxTimeMS Success]: maxTimeMS is accepted with valid
# non-negative numeric values that represent integers within int32 range.
MAX_TIME_MS_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_time_ms_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": 0,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=0 means no time limit and should succeed",
    ),
    CommandTestCase(
        "max_time_ms_small_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": 1000,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=1000 (int32) should succeed",
    ),
    CommandTestCase(
        "max_time_ms_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": INT32_MAX,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS at the int32 maximum should succeed",
    ),
    CommandTestCase(
        "max_time_ms_double_whole",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": 1000.0,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as whole-number double should succeed",
    ),
    CommandTestCase(
        "max_time_ms_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": Int64(INT32_MAX),
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as Int64 at int32 max should succeed",
    ),
    CommandTestCase(
        "max_time_ms_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": Decimal128("1000"),
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as Decimal128 should succeed",
    ),
    CommandTestCase(
        "max_time_ms_double_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as double -0.0 should be treated as 0",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as Decimal128 -0 should be treated as 0",
    ),
    CommandTestCase(
        "max_time_ms_double_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DOUBLE_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as double 0.0 should succeed",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as Decimal128 0 should succeed",
    ),
    CommandTestCase(
        "max_time_ms_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": None,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=null should be treated as absent and succeed",
    ),
]

# Property [maxTimeMS Type Errors]: non-numeric, non-null types produce a
# type-mismatch error.
MAX_TIME_MS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"max_time_ms_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"maxTimeMS={id} should produce a type-mismatch error",
    )
    for id, val in [
        ("string", "hello"),
        ("bool", True),
        ("array", [1]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("binary", Binary(b"x")),
        ("regex", Regex("a", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("datetime", datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)),
    ]
]

# Property [maxTimeMS Value Errors]: negative values and values exceeding
# INT32_MAX produce a bad-value error; non-integer numeric values produce
# a failed-to-parse error.
MAX_TIME_MS_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_time_ms_negative_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative int maxTimeMS should produce a bad-value error",
    ),
    CommandTestCase(
        "max_time_ms_negative_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": -1.0,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative double maxTimeMS should produce a bad-value error",
    ),
    CommandTestCase(
        "max_time_ms_negative_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": Decimal128("-1"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative Decimal128 maxTimeMS should produce a bad-value error",
    ),
    CommandTestCase(
        "max_time_ms_exceeds_int32_max_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": Int64(INT32_MAX + 1),
        },
        error_code=BAD_VALUE_ERROR,
        msg="Int64 exceeding INT32_MAX should produce a bad-value error",
    ),
    CommandTestCase(
        "max_time_ms_exceeds_int32_max_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": float(INT32_OVERFLOW),
        },
        error_code=BAD_VALUE_ERROR,
        msg="Double exceeding INT32_MAX should produce a bad-value error",
    ),
    CommandTestCase(
        "max_time_ms_exceeds_int32_max_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": Decimal128(str(INT32_OVERFLOW)),
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 exceeding INT32_MAX should produce a bad-value error",
    ),
    CommandTestCase(
        "max_time_ms_fractional_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": 1.5,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Fractional double maxTimeMS should produce a failed-to-parse error",
    ),
    CommandTestCase(
        "max_time_ms_fractional_double_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": 0.5,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Double 0.5 maxTimeMS should produce a failed-to-parse error (no truncation)",
    ),
    CommandTestCase(
        "max_time_ms_fractional_decimal128_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_HALF,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 0.5 maxTimeMS should produce a failed-to-parse error (no rounding)",
    ),
    CommandTestCase(
        "max_time_ms_fractional_decimal128_one_and_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_ONE_AND_HALF,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 1.5 maxTimeMS should produce a failed-to-parse error (no rounding)",
    ),
    CommandTestCase(
        "max_time_ms_fractional_decimal128_two_and_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_TWO_AND_HALF,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 2.5 maxTimeMS should produce a failed-to-parse error (no rounding)",
    ),
    CommandTestCase(
        "max_time_ms_double_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": FLOAT_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Double infinity maxTimeMS should produce a failed-to-parse error",
    ),
    CommandTestCase(
        "max_time_ms_double_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": FLOAT_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Double NaN maxTimeMS should produce a failed-to-parse error",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 infinity maxTimeMS should produce a failed-to-parse error",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 NaN maxTimeMS should produce a failed-to-parse error",
    ),
    CommandTestCase(
        "max_time_ms_double_negative_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": FLOAT_NEGATIVE_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Double -NaN maxTimeMS should produce a failed-to-parse error",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_negative_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "maxTimeMS": DECIMAL128_NEGATIVE_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 -NaN maxTimeMS should produce a failed-to-parse error",
    ),
]

CONVERT_TO_CAPPED_MAX_TIME_MS_TESTS: list[CommandTestCase] = (
    MAX_TIME_MS_SUCCESS_TESTS + MAX_TIME_MS_TYPE_ERROR_TESTS + MAX_TIME_MS_VALUE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CONVERT_TO_CAPPED_MAX_TIME_MS_TESTS))
def test_convert_to_capped_max_time_ms(database_client, collection, test):
    """Test convertToCapped command maxTimeMS parameter validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
