"""Tests for $setUnion accumulator: type validation errors and mixed types."""

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

# Property [Type Strictness]: each non-array BSON type as the field value must
# produce TYPE_MISMATCH_ERROR.
SETUNION_TYPE_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_error_int32",
        docs=[{"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject int32 field value",
    ),
    AccumulatorTestCase(
        "type_error_int64",
        docs=[{"v": Int64(42)}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject int64 field value",
    ),
    AccumulatorTestCase(
        "type_error_double",
        docs=[{"v": 3.14}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject double field value",
    ),
    AccumulatorTestCase(
        "type_error_decimal128",
        docs=[{"v": Decimal128("1.5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Decimal128 field value",
    ),
    AccumulatorTestCase(
        "type_error_string",
        docs=[{"v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject string field value",
    ),
    AccumulatorTestCase(
        "type_error_bool_true",
        docs=[{"v": True}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject boolean true field value",
    ),
    AccumulatorTestCase(
        "type_error_bool_false",
        docs=[{"v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject boolean false field value",
    ),
    AccumulatorTestCase(
        "type_error_object",
        docs=[{"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject embedded object field value",
    ),
    AccumulatorTestCase(
        "type_error_objectid",
        docs=[{"v": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject ObjectId field value",
    ),
    AccumulatorTestCase(
        "type_error_datetime",
        docs=[{"v": datetime(2023, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject datetime field value",
    ),
    AccumulatorTestCase(
        "type_error_timestamp",
        docs=[{"v": Timestamp(1, 1)}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Timestamp field value",
    ),
    AccumulatorTestCase(
        "type_error_binary",
        docs=[{"v": Binary(b"\x01\x02")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Binary field value",
    ),
    AccumulatorTestCase(
        "type_error_regex",
        docs=[{"v": Regex("abc", "i")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Regex field value",
    ),
    AccumulatorTestCase(
        "type_error_code",
        docs=[{"v": Code("function(){}")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Code field value",
    ),
    AccumulatorTestCase(
        "type_error_minkey",
        docs=[{"v": MinKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject MinKey field value",
    ),
    AccumulatorTestCase(
        "type_error_maxkey",
        docs=[{"v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject MaxKey field value",
    ),
    AccumulatorTestCase(
        "type_error_null",
        docs=[{"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject null field value",
    ),
]

# Property [Mixed Array and Non-Array Error]: when a group contains a mix of
# array and non-array values, TYPE_MISMATCH_ERROR is produced.
SETUNION_MIXED_TYPE_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_array_first_then_non_array",
        docs=[{"v": [1, 2]}, {"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should error when array doc is followed by non-array doc",
    ),
    AccumulatorTestCase(
        "mixed_non_array_first_then_array",
        docs=[{"v": 42}, {"v": [1, 2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should error when non-array doc is followed by array doc",
    ),
]

SETUNION_ERROR_TESTS = SETUNION_TYPE_ERROR_TESTS + SETUNION_MIXED_TYPE_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_ERROR_TESTS))
def test_accumulator_setUnion_errors(collection, test_case):
    """Test $setUnion accumulator error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
