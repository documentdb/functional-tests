"""Tests for count command maxTimeMS behavior and type strictness."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
)

# Property [MaxTimeMS Behavior]: maxTimeMS controls the execution time limit
# for the count command.
COUNT_MAX_TIME_MS_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxtimems_zero_int",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": 0},
        expected={"n": 5, "ok": 1.0},
        msg="count with maxTimeMS=0 should mean unbounded (no timeout)",
    ),
    CommandTestCase(
        "maxtimems_neg_zero_double",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"n": 5, "ok": 1.0},
        msg="count with maxTimeMS=-0.0 should be accepted as 0 (unbounded)",
    ),
    CommandTestCase(
        "maxtimems_neg_zero_decimal",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"n": 5, "ok": 1.0},
        msg='count with maxTimeMS=Decimal128("-0") should be accepted as 0 (unbounded)',
    ),
    CommandTestCase(
        "maxtimems_neg_zero_decimal_exponent",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Decimal128("-0E+10"),
        },
        expected={"n": 5, "ok": 1.0},
        msg='count with maxTimeMS=Decimal128("-0E+10") should be accepted as 0 (unbounded)',
    ),
]

# Property [Type Strictness: maxTimeMS (accepted)]: int32, int64, whole-number
# double, and integer-valued Decimal128 are accepted for maxTimeMS.
COUNT_TYPE_STRICTNESS_MAXTIMEMS_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_maxtimems_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": 1000},
        expected={"n": 1, "ok": 1.0},
        msg="count should accept int32 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": Int64(1000)},
        expected={"n": 1, "ok": 1.0},
        msg="count should accept Int64 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_whole_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": 1000.0},
        expected={"n": 1, "ok": 1.0},
        msg="count should accept whole-number double for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_whole_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Decimal128("1000"),
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should accept integer-valued Decimal128 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": INT32_MAX},
        expected={"n": 1, "ok": 1.0},
        msg="count should accept int32 maximum value for maxTimeMS",
    ),
]

# Property [Type Strictness: maxTimeMS (type rejected)]: all non-numeric BSON
# types produce a TypeMismatch error for maxTimeMS.
COUNT_TYPE_STRICTNESS_MAXTIMEMS_TYPE_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_maxtimems_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": "hello"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject string for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject bool for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject array for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject object for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject ObjectId for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject datetime for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Timestamp(1, 1),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Timestamp for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Binary(b"\x01\x02"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Binary for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Regex("^abc"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Regex for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Code("function(){}"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Code for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Code("function(){}", {"x": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Code with scope for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject MinKey for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject MaxKey for maxTimeMS",
    ),
]

# Property [Type Strictness: maxTimeMS (representability rejected)]: fractional
# values, NaN, Infinity, and values exceeding int64 range produce a
# FailedToParse error for maxTimeMS.
COUNT_TYPE_STRICTNESS_MAXTIMEMS_REPRESENTABILITY_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_maxtimems_fractional_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": 1.5},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject fractional double for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_fractional_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": DECIMAL128_ONE_AND_HALF,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject fractional Decimal128 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_nan_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": FLOAT_NAN},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject NaN double for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_neg_nan_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": FLOAT_NEGATIVE_NAN},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject -NaN double for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_nan_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": DECIMAL128_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject NaN Decimal128 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_neg_nan_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject -NaN Decimal128 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_infinity_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": FLOAT_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Infinity double for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_neg_infinity_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject -Infinity double for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_infinity_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": DECIMAL128_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Infinity Decimal128 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_neg_infinity_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject -Infinity Decimal128 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_exceeds_int64_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Decimal128("9999999999999999999999"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="count should reject Decimal128 exceeding int64 range for maxTimeMS",
    ),
]

# Property [Type Strictness: maxTimeMS (range rejected)]: negative values and
# values exceeding the int32 maximum (but within int64) produce a BadValue error for
# maxTimeMS.
COUNT_TYPE_STRICTNESS_MAXTIMEMS_RANGE_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_maxtimems_negative_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "maxTimeMS": -1},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject negative int32 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_negative_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Int64(-100),
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject negative Int64 for maxTimeMS",
    ),
    CommandTestCase(
        "type_maxtimems_exceeds_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "maxTimeMS": Int64(INT32_OVERFLOW),
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject values exceeding the int32 max for maxTimeMS",
    ),
]

COUNT_TYPE_STRICTNESS_MAXTIMEMS_TESTS = (
    COUNT_TYPE_STRICTNESS_MAXTIMEMS_ACCEPTED_TESTS
    + COUNT_TYPE_STRICTNESS_MAXTIMEMS_TYPE_REJECTED_TESTS
    + COUNT_TYPE_STRICTNESS_MAXTIMEMS_REPRESENTABILITY_REJECTED_TESTS
    + COUNT_TYPE_STRICTNESS_MAXTIMEMS_RANGE_REJECTED_TESTS
)

COUNT_MAX_TIME_MS_ALL_TESTS: list[CommandTestCase] = (
    COUNT_MAX_TIME_MS_BEHAVIOR_TESTS + COUNT_TYPE_STRICTNESS_MAXTIMEMS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_MAX_TIME_MS_ALL_TESTS))
def test_count_max_time_ms(database_client, collection, test):
    """Test count command maxTimeMS behavior."""
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
