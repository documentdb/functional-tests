"""Tests for listCollections maxTimeMS behavior."""

import uuid
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
)

# Property [maxTimeMS Accepted Types]: maxTimeMS accepts whole-number
# values of int32, Int64, double, and Decimal128, and maxTimeMS=0 or
# negative zero means no timeout.
MAX_TIME_MS_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_int32",
        command={"listCollections": 1, "maxTimeMS": 1000},
        msg="maxTimeMS=1000 (int32) should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_int64",
        command={"listCollections": 1, "maxTimeMS": Int64(1000)},
        msg="maxTimeMS=Int64(1000) should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_double",
        command={"listCollections": 1, "maxTimeMS": 1000.0},
        msg="maxTimeMS=1000.0 (double) should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_decimal128",
        command={"listCollections": 1, "maxTimeMS": Decimal128("1000")},
        msg="maxTimeMS=Decimal128('1000') should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_zero_no_timeout",
        command={"listCollections": 1, "maxTimeMS": 0},
        msg="maxTimeMS=0 should succeed with no time limit",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_negative_zero",
        command={"listCollections": 1, "maxTimeMS": DOUBLE_NEGATIVE_ZERO},
        msg="maxTimeMS=-0.0 should be treated as 0 (no timeout)",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_int32_max",
        command={"listCollections": 1, "maxTimeMS": INT32_MAX},
        msg="maxTimeMS=INT32_MAX should succeed (boundary acceptance)",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
]

# Property [maxTimeMS Parse Errors]: fractional, NaN, and Infinity
# numeric values produce FAILED_TO_PARSE_ERROR because maxTimeMS
# requires a whole integer.
MAX_TIME_MS_PARSE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": 2.5},
        msg="maxTimeMS=2.5 (double) should produce FAILED_TO_PARSE_ERROR",
        id="fractional_double",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": DECIMAL128_TWO_AND_HALF},
        msg="maxTimeMS=Decimal128('2.5') should produce FAILED_TO_PARSE_ERROR",
        id="fractional_decimal128",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": FLOAT_NAN},
        msg="maxTimeMS=NaN (float) should produce FAILED_TO_PARSE_ERROR",
        id="nan_float",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": DECIMAL128_NAN},
        msg="maxTimeMS=NaN (Decimal128) should produce FAILED_TO_PARSE_ERROR",
        id="nan_decimal128",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": FLOAT_INFINITY},
        msg="maxTimeMS=Infinity (float) should produce FAILED_TO_PARSE_ERROR",
        id="infinity_float",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": FLOAT_NEGATIVE_INFINITY},
        msg="maxTimeMS=-Infinity (float) should produce FAILED_TO_PARSE_ERROR",
        id="neg_infinity_float",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": DECIMAL128_INFINITY},
        msg="maxTimeMS=Infinity (Decimal128) should produce FAILED_TO_PARSE_ERROR",
        id="infinity_decimal128",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": DECIMAL128_NEGATIVE_INFINITY},
        msg="maxTimeMS=-Infinity (Decimal128) should produce FAILED_TO_PARSE_ERROR",
        id="neg_infinity_decimal128",
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]

# Property [maxTimeMS Range Errors]: values exceeding INT32_MAX or
# negative values produce BAD_VALUE_ERROR.
MAX_TIME_MS_RANGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": INT32_MAX + 1},
        msg="maxTimeMS=INT32_MAX+1 (int) should produce BAD_VALUE_ERROR",
        id="exceeds_int32_max_int",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": Int64(INT32_MAX + 1)},
        msg="maxTimeMS=INT32_MAX+1 (Int64) should produce BAD_VALUE_ERROR",
        id="exceeds_int32_max_int64",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": float(INT32_MAX + 1)},
        msg="maxTimeMS=INT32_MAX+1 (double) should produce BAD_VALUE_ERROR",
        id="exceeds_int32_max_double",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": Decimal128(str(INT32_MAX + 1))},
        msg="maxTimeMS=INT32_MAX+1 (Decimal128) should produce BAD_VALUE_ERROR",
        id="exceeds_int32_max_decimal128",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": -1},
        msg="maxTimeMS=-1 (int) should produce BAD_VALUE_ERROR",
        id="negative_int",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "maxTimeMS": Int64(-1)},
        msg="maxTimeMS=-1 (Int64) should produce BAD_VALUE_ERROR",
        id="negative_int64",
        error_code=BAD_VALUE_ERROR,
    ),
]

# Property [maxTimeMS Type Errors]: when maxTimeMS is a non-numeric
# BSON type, the command produces a TYPE_MISMATCH_ERROR.
MAX_TIME_MS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="max_time_ms_bool",
        command={"listCollections": 1, "maxTimeMS": True},
        msg="maxTimeMS=bool should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_string",
        command={"listCollections": 1, "maxTimeMS": "hello"},
        msg="maxTimeMS=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_array",
        command={"listCollections": 1, "maxTimeMS": [1]},
        msg="maxTimeMS=array should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_object",
        command={"listCollections": 1, "maxTimeMS": {"a": 1}},
        msg="maxTimeMS=object should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_objectid",
        command=lambda _: {"listCollections": 1, "maxTimeMS": ObjectId()},
        msg="maxTimeMS=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_datetime",
        command={
            "listCollections": 1,
            "maxTimeMS": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        msg="maxTimeMS=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_timestamp",
        command={"listCollections": 1, "maxTimeMS": Timestamp(1, 1)},
        msg="maxTimeMS=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_binary",
        command={"listCollections": 1, "maxTimeMS": Binary(b"hello")},
        msg="maxTimeMS=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_binary_uuid",
        command=lambda _: {
            "listCollections": 1,
            "maxTimeMS": Binary(uuid.uuid4().bytes, 4),
        },
        msg="maxTimeMS=Binary subtype 4 (UUID) should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_regex",
        command={"listCollections": 1, "maxTimeMS": Regex(".*")},
        msg="maxTimeMS=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_code",
        command={"listCollections": 1, "maxTimeMS": Code("function(){}")},
        msg="maxTimeMS=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_code_with_scope",
        command={"listCollections": 1, "maxTimeMS": Code("function(){}", {"x": 1})},
        msg="maxTimeMS=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_minkey",
        command={"listCollections": 1, "maxTimeMS": MinKey()},
        msg="maxTimeMS=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="max_time_ms_maxkey",
        command={"listCollections": 1, "maxTimeMS": MaxKey()},
        msg="maxTimeMS=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

MAX_TIME_MS_TESTS: list[CommandTestCase] = (
    MAX_TIME_MS_SUCCESS_TESTS
    + MAX_TIME_MS_PARSE_ERROR_TESTS
    + MAX_TIME_MS_RANGE_ERROR_TESTS
    + MAX_TIME_MS_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(MAX_TIME_MS_TESTS))
def test_listCollections_max_time_ms(database_client, collection, test):
    """Test listCollections maxTimeMS behavior."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
