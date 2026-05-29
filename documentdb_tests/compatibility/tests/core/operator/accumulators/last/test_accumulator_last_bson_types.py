"""Tests for $last accumulator: BSON type passthrough."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Type Passthrough]: $last returns the last value in a group
# unchanged, preserving its exact BSON type without coercion.
LAST_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 3.14}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 3.14}],
        msg="$last should return double value unchanged",
    ),
    AccumulatorTestCase(
        "bson_int32",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 42}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$last should return int32 value unchanged",
    ),
    AccumulatorTestCase(
        "bson_int64",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Int64(9223372036854775807)}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(9223372036854775807)}],
        msg="$last should return int64 value unchanged",
    ),
    AccumulatorTestCase(
        "bson_decimal128",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": Decimal128("123.456")},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("123.456")}],
        msg="$last should return Decimal128 value unchanged",
    ),
    AccumulatorTestCase(
        "bson_string",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": "hello"}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$last should return string value unchanged",
    ),
    AccumulatorTestCase(
        "bson_bool_true",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": True}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$last should return boolean true unchanged",
    ),
    AccumulatorTestCase(
        "bson_bool_false",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": False}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$last should return boolean false unchanged",
    ),
    AccumulatorTestCase(
        "bson_date",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$last should return datetime value unchanged",
    ),
    AccumulatorTestCase(
        "bson_null",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": None}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$last should return null value unchanged",
    ),
    AccumulatorTestCase(
        "bson_object",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": {"nested": "doc"}}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"nested": "doc"}}],
        msg="$last should return embedded document unchanged",
    ),
    AccumulatorTestCase(
        "bson_array",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": [1, 2, 3]}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$last should return entire array unchanged without traversal",
    ),
    AccumulatorTestCase(
        "bson_binary",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Binary(b"\x00\x01\x02")}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x00\x01\x02"}],
        msg="$last should return Binary value unchanged",
    ),
    AccumulatorTestCase(
        "bson_objectid",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$last should return ObjectId unchanged",
    ),
    AccumulatorTestCase(
        "bson_regex",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Regex("^abc", "i")}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("^abc", "i")}],
        msg="$last should return Regex unchanged",
    ),
    AccumulatorTestCase(
        "bson_timestamp",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Timestamp(1, 1)}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(1, 1)}],
        msg="$last should return Timestamp unchanged",
    ),
    AccumulatorTestCase(
        "bson_minkey",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": MinKey()}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MinKey()}}],
        msg="$last should return MinKey wrapped as object via runCommand",
    ),
    AccumulatorTestCase(
        "bson_maxkey",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": MaxKey()}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MaxKey()}}],
        msg="$last should return MaxKey wrapped as object via runCommand",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LAST_BSON_TYPE_TESTS))
def test_accumulator_last_bson_types(collection, test_case: AccumulatorTestCase):
    """Test $last accumulator BSON type passthrough."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
