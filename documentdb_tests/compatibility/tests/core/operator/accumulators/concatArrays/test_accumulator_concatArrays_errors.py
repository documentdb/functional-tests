"""Tests for $concatArrays accumulator: null handling, type rejection, and mixed invalid errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Handling]: null field values produce TYPE_MISMATCH_ERROR in
# accumulator context.
CONCATARRAYS_NULL_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_single",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null field value",
    ),
    AccumulatorTestCase(
        "null_all",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when all field values are null",
    ),
    AccumulatorTestCase(
        "null_after_array",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": None},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null even after valid arrays",
    ),
    AccumulatorTestCase(
        "null_before_array",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2, "v": [1, 2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null even before valid arrays",
    ),
]

# Property [Non-Array Type Rejection]: every non-array, non-null BSON type
# produces TYPE_MISMATCH_ERROR.
CONCATARRAYS_TYPE_REJECTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_reject_string",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject string field value",
    ),
    AccumulatorTestCase(
        "type_reject_int32",
        docs=[{"_id": 1, "v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject int32 field value",
    ),
    AccumulatorTestCase(
        "type_reject_int64",
        docs=[{"_id": 1, "v": Int64(42)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Int64 field value",
    ),
    AccumulatorTestCase(
        "type_reject_double",
        docs=[{"_id": 1, "v": 3.14}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject double field value",
    ),
    AccumulatorTestCase(
        "type_reject_decimal128",
        docs=[{"_id": 1, "v": Decimal128("1.5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Decimal128 field value",
    ),
    AccumulatorTestCase(
        "type_reject_bool_true",
        docs=[{"_id": 1, "v": True}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean True field value",
    ),
    AccumulatorTestCase(
        "type_reject_bool_false",
        docs=[{"_id": 1, "v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean False field value",
    ),
    AccumulatorTestCase(
        "type_reject_object",
        docs=[{"_id": 1, "v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject embedded document field value",
    ),
    AccumulatorTestCase(
        "type_reject_empty_object",
        docs=[{"_id": 1, "v": {}}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject empty document field value",
    ),
    AccumulatorTestCase(
        "type_reject_objectid",
        docs=[{"_id": 1, "v": ObjectId()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject ObjectId field value",
    ),
    AccumulatorTestCase(
        "type_reject_datetime",
        docs=[{"_id": 1, "v": datetime(2023, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject datetime field value",
    ),
    AccumulatorTestCase(
        "type_reject_binary",
        docs=[{"_id": 1, "v": Binary(b"\x01\x02")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Binary field value",
    ),
    AccumulatorTestCase(
        "type_reject_regex",
        docs=[{"_id": 1, "v": Regex("abc", "i")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Regex field value",
    ),
    AccumulatorTestCase(
        "type_reject_code",
        docs=[{"_id": 1, "v": Code("function(){}")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Code field value",
    ),
    AccumulatorTestCase(
        "type_reject_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1, 1)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Timestamp field value",
    ),
    AccumulatorTestCase(
        "type_reject_minkey",
        docs=[{"_id": 1, "v": MinKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MinKey field value",
    ),
    AccumulatorTestCase(
        "type_reject_maxkey",
        docs=[{"_id": 1, "v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MaxKey field value",
    ),
]

# Property [Mixed Valid and Invalid]: when one document has a valid array and
# another has an invalid type, the error is raised.
CONCATARRAYS_MIXED_INVALID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_array_and_string",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": "hello"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when mixing array and string values",
    ),
    AccumulatorTestCase(
        "mixed_array_and_integer",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": 42},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when mixing array and integer values",
    ),
]

CONCATARRAYS_ERROR_TESTS = (
    CONCATARRAYS_NULL_ERROR_TESTS
    + CONCATARRAYS_TYPE_REJECTION_TESTS
    + CONCATARRAYS_MIXED_INVALID_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_ERROR_TESTS))
def test_accumulator_concatArrays_errors(collection, test_case):
    """Test $concatArrays error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
