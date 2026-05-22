"""Tests for $last accumulator: return type verification via $type projection.

Verifies that $last preserves the exact BSON type of the last document's value
without any coercion (unlike numeric accumulators which promote types).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Return Type Preservation]: $last preserves the BSON type of the
# last value, verified via $type projection.
LAST_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_int32",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 42}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 42, "type": "int"}],
        msg="$last should preserve int32 type",
    ),
    AccumulatorTestCase(
        "type_int64",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Int64(42)}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Int64(42), "type": "long"}],
        msg="$last should preserve int64 type",
    ),
    AccumulatorTestCase(
        "type_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 3.14}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 3.14, "type": "double"}],
        msg="$last should preserve double type",
    ),
    AccumulatorTestCase(
        "type_decimal128",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Decimal128("3.14")}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Decimal128("3.14"), "type": "decimal"}],
        msg="$last should preserve Decimal128 type",
    ),
    AccumulatorTestCase(
        "type_string",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": "hello"}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": "hello", "type": "string"}],
        msg="$last should preserve string type",
    ),
    AccumulatorTestCase(
        "type_bool",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": True}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": True, "type": "bool"}],
        msg="$last should preserve bool type",
    ),
    AccumulatorTestCase(
        "type_date",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": datetime(2024, 1, 1, tzinfo=timezone.utc), "type": "date"}],
        msg="$last should preserve date type",
    ),
    AccumulatorTestCase(
        "type_null",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": None}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": None, "type": "null"}],
        msg="$last should preserve null type",
    ),
    AccumulatorTestCase(
        "type_object",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": {"a": 1}}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": {"a": 1}, "type": "object"}],
        msg="$last should preserve object type",
    ),
    AccumulatorTestCase(
        "type_array",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": [1, 2]}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": [1, 2], "type": "array"}],
        msg="$last should preserve array type",
    ),
    AccumulatorTestCase(
        "type_binary",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Binary(b"\x01")}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": b"\x01", "type": "binData"}],
        msg="$last should preserve Binary type",
    ),
    AccumulatorTestCase(
        "type_objectid",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": ObjectId("507f1f77bcf86cd799439011"), "type": "objectId"}],
        msg="$last should preserve ObjectId type",
    ),
    AccumulatorTestCase(
        "type_regex",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Regex("abc", "i")}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Regex("abc", "i"), "type": "regex"}],
        msg="$last should preserve Regex type",
    ),
    AccumulatorTestCase(
        "type_code",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Code("function(){}")}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": "function(){}", "type": "string"}],
        msg="$last should return Code as string via runCommand",
    ),
    AccumulatorTestCase(
        "type_timestamp",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Timestamp(1, 1)}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Timestamp(1, 1), "type": "timestamp"}],
        msg="$last should preserve Timestamp type",
    ),
    AccumulatorTestCase(
        "type_minkey",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": MinKey()}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": {"": MinKey()}, "type": "object"}],
        msg="$last should return MinKey wrapped as object via runCommand",
    ),
    AccumulatorTestCase(
        "type_maxkey",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": MaxKey()}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": {"": MaxKey()}, "type": "object"}],
        msg="$last should return MaxKey wrapped as object via runCommand",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LAST_RETURN_TYPE_TESTS))
def test_last_group_types(collection, test_case: AccumulatorTestCase):
    """Test $last return type preservation via $type projection."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
