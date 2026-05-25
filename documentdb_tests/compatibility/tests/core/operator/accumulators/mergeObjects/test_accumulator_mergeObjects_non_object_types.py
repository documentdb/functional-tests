"""Tests for $mergeObjects accumulator: non-object type error behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import MERGE_OBJECTS_NON_OBJECT_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Object Type Rejection]: $mergeObjects rejects non-object,
# non-null BSON types with an error, unlike numeric accumulators which ignore
# non-numeric types silently.
MERGE_OBJECTS_NON_OBJECT_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "non_object_string",
        docs=[{"v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject string values",
    ),
    AccumulatorTestCase(
        "non_object_int32",
        docs=[{"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject int32 values",
    ),
    AccumulatorTestCase(
        "non_object_int64",
        docs=[{"v": Int64(42)}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject Int64 values",
    ),
    AccumulatorTestCase(
        "non_object_double",
        docs=[{"v": 3.14}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject double values",
    ),
    AccumulatorTestCase(
        "non_object_decimal128",
        docs=[{"v": Decimal128("1.5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject Decimal128 values",
    ),
    AccumulatorTestCase(
        "non_object_bool_true",
        docs=[{"v": True}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject boolean True",
    ),
    AccumulatorTestCase(
        "non_object_bool_false",
        docs=[{"v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject boolean False",
    ),
    AccumulatorTestCase(
        "non_object_datetime",
        docs=[{"v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject datetime values",
    ),
    AccumulatorTestCase(
        "non_object_objectid",
        docs=[{"v": ObjectId("000000000000000000000000")}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject ObjectId values",
    ),
    AccumulatorTestCase(
        "non_object_binary",
        docs=[{"v": Binary(b"\x01\x02")}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject Binary values",
    ),
    AccumulatorTestCase(
        "non_object_regex",
        docs=[{"v": Regex("abc", "i")}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject Regex values",
    ),
    AccumulatorTestCase(
        "non_object_code",
        docs=[{"v": Code("function(){}")}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject Code values",
    ),
    AccumulatorTestCase(
        "non_object_timestamp",
        docs=[{"v": Timestamp(1, 1)}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject Timestamp values",
    ),
    AccumulatorTestCase(
        "non_object_minkey",
        docs=[{"v": MinKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject MinKey values",
    ),
    AccumulatorTestCase(
        "non_object_maxkey",
        docs=[{"v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject MaxKey values",
    ),
    AccumulatorTestCase(
        "non_object_array",
        docs=[{"v": [1, 2, 3]}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject array values",
    ),
    AccumulatorTestCase(
        "non_object_empty_array",
        docs=[{"v": []}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject empty array values",
    ),
    AccumulatorTestCase(
        "non_object_numeric_string",
        docs=[{"v": "123"}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject numeric strings without coercion",
    ),
]

# Property [Non-Object After Valid Objects]: $mergeObjects errors when a
# non-object value appears after valid objects in the group.
MERGE_OBJECTS_NON_OBJECT_AFTER_VALID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "non_object_after_valid_string",
        docs=[{"v": {"a": 1}}, {"v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should error when string appears after valid object",
    ),
    AccumulatorTestCase(
        "non_object_after_valid_int",
        docs=[{"v": {"a": 1}}, {"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should error when int appears after valid object",
    ),
    AccumulatorTestCase(
        "non_object_after_valid_array",
        docs=[{"v": {"a": 1}}, {"v": [1, 2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should error when array appears after valid object",
    ),
    AccumulatorTestCase(
        "non_object_after_valid_bool",
        docs=[{"v": {"a": 1}}, {"v": True}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should error when bool appears after valid object",
    ),
]

# Property [Non-Object Constant Expression]: $mergeObjects errors when a
# constant expression resolves to a non-object, non-null type.
MERGE_OBJECTS_NON_OBJECT_CONSTANT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_string",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "hello"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject constant string expression",
    ),
    AccumulatorTestCase(
        "constant_int",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": 42}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject constant int expression",
    ),
    AccumulatorTestCase(
        "constant_bool",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": True}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should reject constant bool expression",
    ),
]

MERGE_OBJECTS_NON_OBJECT_TESTS = (
    MERGE_OBJECTS_NON_OBJECT_TYPE_TESTS
    + MERGE_OBJECTS_NON_OBJECT_AFTER_VALID_TESTS
    + MERGE_OBJECTS_NON_OBJECT_CONSTANT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MERGE_OBJECTS_NON_OBJECT_TESTS))
def test_accumulator_mergeObjects_non_object_types(collection, test_case: AccumulatorTestCase):
    """Test $mergeObjects non-object type error behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)  # type: ignore[arg-type]
