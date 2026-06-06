"""Tests for getMore field value validation."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CURSOR_NOT_FOUND_ERROR,
    FAILED_TO_PARSE_ERROR,
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
    INT32_MAX,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Cursor ID Not Found]: any int64 value that does not correspond to
# an existing cursor produces CURSOR_NOT_FOUND_ERROR, including 0, -1, and
# boundary values.
GETMORE_CURSOR_ID_NOT_FOUND_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "cursor_id_not_found_zero",
        cursor_count=0,
        command=lambda ctx: {"getMore": INT64_ZERO, "collection": ctx.collection},
        error_code=CURSOR_NOT_FOUND_ERROR,
        msg="getMore should produce CursorNotFound for cursor ID 0",
    ),
    CursorCommandTestCase(
        "cursor_id_not_found_neg_one",
        cursor_count=0,
        command=lambda ctx: {"getMore": Int64(-1), "collection": ctx.collection},
        error_code=CURSOR_NOT_FOUND_ERROR,
        msg="getMore should produce CursorNotFound for cursor ID -1",
    ),
    CursorCommandTestCase(
        "cursor_id_not_found_int64_max",
        cursor_count=0,
        command=lambda ctx: {"getMore": INT64_MAX, "collection": ctx.collection},
        error_code=CURSOR_NOT_FOUND_ERROR,
        msg="getMore should produce CursorNotFound for cursor ID at int64 max",
    ),
    CursorCommandTestCase(
        "cursor_id_not_found_int64_min",
        cursor_count=0,
        command=lambda ctx: {"getMore": INT64_MIN, "collection": ctx.collection},
        error_code=CURSOR_NOT_FOUND_ERROR,
        msg="getMore should produce CursorNotFound for cursor ID at int64 min",
    ),
]

# Property [batchSize Negative Value Error]: negative numeric values that
# coerce to a negative integer produce BAD_VALUE_ERROR.
GETMORE_BATCH_SIZE_NEGATIVE_VALUE_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "batch_size_neg_int32",
        cursor_count=0,
        command=lambda ctx: {"getMore": Int64(1), "collection": ctx.collection, "batchSize": -1},
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject negative int32 batchSize",
    ),
    CursorCommandTestCase(
        "batch_size_neg_int64",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "batchSize": Int64(-5),
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject negative int64 batchSize",
    ),
    CursorCommandTestCase(
        "batch_size_neg_double",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "batchSize": -1.5,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject negative double -1.5 which truncates to -1",
    ),
    # Decimal128 -0.50001 rounds to -1 via banker's rounding.
    CursorCommandTestCase(
        "batch_size_neg_decimal_below_half",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "batchSize": Decimal128("-0.50001"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject Decimal128 -0.50001 which rounds to -1",
    ),
    CursorCommandTestCase(
        "batch_size_neg_inf_double",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "batchSize": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject negative infinity double batchSize",
    ),
    CursorCommandTestCase(
        "batch_size_neg_inf_decimal",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "batchSize": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject negative infinity Decimal128 batchSize",
    ),
]

# Property [maxTimeMS Non-Integer Error]: numeric values that do not represent
# a whole integer produce FAILED_TO_PARSE_ERROR because maxTimeMS requires an
# integer.
GETMORE_MAX_TIME_MS_NON_INTEGER_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "max_time_ms_non_int_double_2_5",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": 2.5,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject fractional double 2.5 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_double_0_1",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": 0.1,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject fractional double 0.1 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_double_0_9",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": 0.9,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject fractional double 0.9 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_decimal_fractional",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": DECIMAL128_ONE_AND_HALF,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject fractional Decimal128 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_double_nan",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": FLOAT_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject double NaN as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_double_neg_nan",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": FLOAT_NEGATIVE_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject double -NaN as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_double_infinity",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": FLOAT_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject double Infinity as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_double_neg_infinity",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject double -Infinity as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_decimal_nan",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": DECIMAL128_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject Decimal128 NaN as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_decimal_neg_nan",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject Decimal128 -NaN as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_decimal_infinity",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": DECIMAL128_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject Decimal128 Infinity as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_decimal_neg_infinity",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject Decimal128 -Infinity as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_non_int_decimal_overflow_int64",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": Decimal128("1E+20"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="getMore should reject Decimal128 that overflows int64 as maxTimeMS",
    ),
]

# Property [maxTimeMS Range Error]: integer values above 2147483647 or below 0
# produce BAD_VALUE_ERROR.
GETMORE_MAX_TIME_MS_RANGE_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "max_time_ms_range_above_int32_max",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": INT32_MAX + 1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject maxTimeMS above max int32",
    ),
    CursorCommandTestCase(
        "max_time_ms_range_large_int64",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": INT64_MAX,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject maxTimeMS at int64 max",
    ),
    CursorCommandTestCase(
        "max_time_ms_range_negative_one",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject negative maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_range_negative_int64",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": INT64_MIN,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject maxTimeMS at int64 min",
    ),
    CursorCommandTestCase(
        "max_time_ms_range_double_above_int32_max",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": float(INT32_MAX + 1),
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject whole-integer double above max int32 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_range_double_negative",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": -1.0,
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject whole-integer negative double as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_range_decimal_above_int32_max",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": Decimal128(str(INT32_MAX + 1)),
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject whole-integer Decimal128 above max int32 as maxTimeMS",
    ),
    CursorCommandTestCase(
        "max_time_ms_range_decimal_negative",
        cursor_count=0,
        command=lambda ctx: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": Decimal128("-1"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="getMore should reject whole-integer negative Decimal128 as maxTimeMS",
    ),
]

GETMORE_FIELD_VALUE_ERROR_TESTS = (
    GETMORE_CURSOR_ID_NOT_FOUND_TESTS
    + GETMORE_BATCH_SIZE_NEGATIVE_VALUE_ERROR_TESTS
    + GETMORE_MAX_TIME_MS_NON_INTEGER_ERROR_TESTS
    + GETMORE_MAX_TIME_MS_RANGE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_FIELD_VALUE_ERROR_TESTS))
def test_getMore_field_value_errors(collection, test_case: CursorCommandTestCase):
    """Test getMore field value validation."""
    collection.insert_many([{"_id": i, "v": i} for i in range(5)])
    cursors = open_find_cursors(
        collection, test_case.cursor_count, batch_size=test_case.find_batch_size
    )
    ctx = CursorCommandContext.from_collection(collection, cursors=cursors)
    result = execute_command(collection, test_case.build_command(ctx))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
