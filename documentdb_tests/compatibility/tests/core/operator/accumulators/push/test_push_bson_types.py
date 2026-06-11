"""Tests for $push accumulator: BSON type preservation and type verification."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Type Preservation]: $push collects and preserves every
# non-deprecated BSON type in the output array without coercion or
# normalization.
PUSH_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_int32",
        docs=[{"v": 42}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [42]}],
        msg="$push should preserve int32 value in output array",
    ),
    AccumulatorTestCase(
        "bson_int64",
        docs=[{"v": Int64(42)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Int64(42)]}],
        msg="$push should preserve Int64 value in output array",
    ),
    AccumulatorTestCase(
        "bson_double",
        docs=[{"v": 3.14}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [3.14]}],
        msg="$push should preserve double value in output array",
    ),
    AccumulatorTestCase(
        "bson_decimal128",
        docs=[{"v": Decimal128("1.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Decimal128("1.5")]}],
        msg="$push should preserve Decimal128 value in output array",
    ),
    AccumulatorTestCase(
        "bson_string",
        docs=[{"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": ["hello"]}],
        msg="$push should preserve string value in output array",
    ),
    AccumulatorTestCase(
        "bson_bool_true",
        docs=[{"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [True]}],
        msg="$push should preserve boolean true in output array",
    ),
    AccumulatorTestCase(
        "bson_bool_false",
        docs=[{"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [False]}],
        msg="$push should preserve boolean false in output array",
    ),
    AccumulatorTestCase(
        "bson_datetime",
        docs=[{"v": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc)]}],
        msg="$push should preserve datetime value in output array",
    ),
    AccumulatorTestCase(
        "bson_timestamp",
        docs=[{"v": Timestamp(1, 1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Timestamp(1, 1)]}],
        msg="$push should preserve Timestamp value in output array",
    ),
    AccumulatorTestCase(
        "bson_objectid",
        docs=[{"v": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [ObjectId("507f1f77bcf86cd799439011")]}],
        msg="$push should preserve ObjectId value in output array",
    ),
    AccumulatorTestCase(
        "bson_binary",
        docs=[{"v": Binary(b"\x01\x02\x03")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [b"\x01\x02\x03"]}],
        msg="$push should preserve Binary value in output array",
    ),
    AccumulatorTestCase(
        "bson_regex",
        docs=[{"v": Regex("abc", "i")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Regex("abc", "i")]}],
        msg="$push should preserve Regex value in output array",
    ),
    AccumulatorTestCase(
        "bson_code",
        docs=[{"v": Code("function(){}")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Code("function(){}")]}],
        msg="$push should preserve Code value in output array",
    ),
    AccumulatorTestCase(
        "bson_minkey",
        docs=[{"v": MinKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [MinKey()]}],
        msg="$push should preserve MinKey value in output array",
    ),
    AccumulatorTestCase(
        "bson_maxkey",
        docs=[{"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [MaxKey()]}],
        msg="$push should preserve MaxKey value in output array",
    ),
    AccumulatorTestCase(
        "bson_null",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None]}],
        msg="$push should preserve null value in output array",
    ),
    AccumulatorTestCase(
        "bson_object",
        docs=[{"v": {"a": 1, "b": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": 1, "b": 2}]}],
        msg="$push should preserve embedded object in output array",
    ),
    AccumulatorTestCase(
        "bson_empty_object",
        docs=[{"v": {}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{}]}],
        msg="$push should preserve empty object in output array",
    ),
    AccumulatorTestCase(
        "bson_array",
        docs=[{"v": [1, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2, 3]]}],
        msg="$push should preserve array value as nested array in output",
    ),
    AccumulatorTestCase(
        "bson_empty_array",
        docs=[{"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[]]}],
        msg="$push should preserve empty array in output array",
    ),
    AccumulatorTestCase(
        "bson_mixed_types",
        docs=[
            {"v": 1, "s": 1},
            {"v": "hello", "s": 2},
            {"v": True, "s": 3},
            {"v": None, "s": 4},
            {"v": [1, 2], "s": 5},
            {"v": {"a": 1}, "s": 6},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, "hello", True, None, [1, 2], {"a": 1}]}],
        msg="$push should preserve all mixed BSON types in correct order",
    ),
    AccumulatorTestCase(
        "bson_all_numeric_types",
        docs=[
            {"v": 1, "s": 1},
            {"v": Int64(2), "s": 2},
            {"v": 3.0, "s": 3},
            {"v": Decimal128("4"), "s": 4},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, Int64(2), 3.0, Decimal128("4")]}],
        msg="$push should preserve all numeric types without promotion or normalization",
    ),
]

# Property [Type Preservation]: $push preserves the exact BSON type of each
# collected value without coercing numerically equivalent values.
PUSH_TYPE_PRESERVATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_int32_vs_int64",
        docs=[{"v": 1, "s": 1}, {"v": Int64(1), "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["int", "long"]}],
        msg="$push should preserve distinct types for int32(1) and Int64(1)",
    ),
    AccumulatorTestCase(
        "type_int32_vs_double",
        docs=[{"v": 0, "s": 1}, {"v": 0.0, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["int", "double"]}],
        msg="$push should preserve distinct types for int32(0) and double(0.0)",
    ),
    AccumulatorTestCase(
        "type_bool_vs_int",
        docs=[{"v": False, "s": 1}, {"v": 0, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["bool", "int"]}],
        msg="$push should preserve distinct types for false and int32(0)",
    ),
    AccumulatorTestCase(
        "type_string_vs_null",
        docs=[{"v": "", "s": 1}, {"v": None, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["string", "null"]}],
        msg="$push should preserve distinct types for empty string and null",
    ),
    AccumulatorTestCase(
        "type_all_numerics_preserved",
        docs=[
            {"v": 1, "s": 1},
            {"v": Int64(1), "s": 2},
            {"v": 1.0, "s": 3},
            {"v": Decimal128("1"), "s": 4},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["int", "long", "double", "decimal"]}],
        msg="$push should preserve all four numeric types without normalization",
    ),
]

PUSH_BSON_TYPE_ALL_TESTS = PUSH_BSON_TYPE_TESTS + PUSH_TYPE_PRESERVATION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(PUSH_BSON_TYPE_ALL_TESTS))
def test_push_bson_types(collection, test_case: AccumulatorTestCase):
    """Test $push BSON type preservation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
