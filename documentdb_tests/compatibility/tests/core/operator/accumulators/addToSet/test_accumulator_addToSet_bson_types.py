"""Tests for $addToSet accumulator BSON type collection and deduplication."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [BSON Type Collection]: $addToSet collects and deduplicates values of every
# non-deprecated BSON type.
ADDTOSET_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_int32",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20]}],
        msg="$addToSet should collect and deduplicate int32 values",
    ),
    AccumulatorTestCase(
        "bson_int64",
        docs=[{"v": Int64(10)}, {"v": Int64(20)}, {"v": Int64(10)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Int64(10), Int64(20)]}],
        msg="$addToSet should collect and deduplicate Int64 values",
    ),
    AccumulatorTestCase(
        "bson_double",
        docs=[{"v": 1.5}, {"v": 2.5}, {"v": 1.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1.5, 2.5]}],
        msg="$addToSet should collect and deduplicate double values",
    ),
    AccumulatorTestCase(
        "bson_decimal128",
        docs=[
            {"v": Decimal128("1.5")},
            {"v": Decimal128("2.5")},
            {"v": Decimal128("1.5")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("1.5"), Decimal128("2.5")]}],
        msg="$addToSet should collect and deduplicate Decimal128 values",
    ),
    AccumulatorTestCase(
        "bson_string",
        docs=[{"v": "abc"}, {"v": "def"}, {"v": "abc"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["abc", "def"]}],
        msg="$addToSet should collect and deduplicate string values",
    ),
    AccumulatorTestCase(
        "bson_bool",
        docs=[{"v": True}, {"v": False}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [True, False]}],
        msg="$addToSet should collect and deduplicate boolean values",
    ),
    AccumulatorTestCase(
        "bson_datetime",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2021, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[
            {
                "result": [
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2021, 1, 1, tzinfo=timezone.utc),
                ]
            }
        ],
        msg="$addToSet should collect and deduplicate datetime values",
    ),
    AccumulatorTestCase(
        "bson_objectid",
        docs=[
            {"v": ObjectId("000000000000000000000001")},
            {"v": ObjectId("000000000000000000000002")},
            {"v": ObjectId("000000000000000000000001")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[
            {
                "result": [
                    ObjectId("000000000000000000000001"),
                    ObjectId("000000000000000000000002"),
                ]
            }
        ],
        msg="$addToSet should collect and deduplicate ObjectId values",
    ),
    AccumulatorTestCase(
        "bson_binary",
        docs=[{"v": Binary(b"\x00")}, {"v": Binary(b"\x01")}, {"v": Binary(b"\x00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [b"\x00", b"\x01"]}],
        msg="$addToSet should collect and deduplicate Binary values",
    ),
    AccumulatorTestCase(
        "bson_regex",
        docs=[{"v": Regex("abc")}, {"v": Regex("def")}, {"v": Regex("abc")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Regex("abc"), Regex("def")]}],
        msg="$addToSet should collect and deduplicate Regex values",
    ),
    AccumulatorTestCase(
        "bson_code",
        docs=[
            {"v": Code("function(){}")},
            {"v": Code("function(){return 1}")},
            {"v": Code("function(){}")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["function(){}", "function(){return 1}"]}],
        msg="$addToSet should collect and deduplicate Code values",
    ),
    AccumulatorTestCase(
        "bson_timestamp",
        docs=[
            {"v": Timestamp(100, 1)},
            {"v": Timestamp(200, 1)},
            {"v": Timestamp(100, 1)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Timestamp(100, 1), Timestamp(200, 1)]}],
        msg="$addToSet should collect and deduplicate Timestamp values",
    ),
    AccumulatorTestCase(
        "bson_minkey",
        docs=[{"v": MinKey()}, {"v": MinKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"": MinKey()}]}],
        msg="$addToSet should deduplicate MinKey values",
    ),
    AccumulatorTestCase(
        "bson_maxkey",
        docs=[{"v": MaxKey()}, {"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"": MaxKey()}]}],
        msg="$addToSet should deduplicate MaxKey values",
    ),
    AccumulatorTestCase(
        "bson_document",
        docs=[{"v": {"x": 1}}, {"v": {"x": 2}}, {"v": {"x": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"x": 1}, {"x": 2}]}],
        msg="$addToSet should collect and deduplicate embedded document values",
    ),
    AccumulatorTestCase(
        "bson_array",
        docs=[{"v": [1, 2]}, {"v": [3, 4]}, {"v": [1, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[1, 2], [3, 4]]}],
        msg="$addToSet should collect and deduplicate array values as single elements",
    ),
    AccumulatorTestCase(
        "bson_null",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should deduplicate null values",
    ),
]

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_BSON_TYPE_TESTS))
def test_accumulator_addToSet_bson_types(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator BSON type collection and deduplication."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])
