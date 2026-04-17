"""
Tests for $gt BSON type wiring.

A representative sample of types to confirm $gt is wired up to the
BSON comparison engine correctly (not exhaustive cross-type matrix).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Timestamp
from bson.codec_options import CodecOptions

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double",
        filter={"a": {"$gt": 5.0}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 5.0}, {"_id": 3, "a": 10.0}],
        expected=[{"_id": 3, "a": 10.0}],
        msg="$gt with double returns docs with value > 5.0",
    ),
    QueryTestCase(
        id="int",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 10}],
        expected=[{"_id": 3, "a": 10}],
        msg="$gt with int returns docs with value > 5",
    ),
    QueryTestCase(
        id="long",
        filter={"a": {"$gt": Int64(5)}},
        doc=[
            {"_id": 1, "a": Int64(1)},
            {"_id": 2, "a": Int64(5)},
            {"_id": 3, "a": Int64(10)},
        ],
        expected=[{"_id": 3, "a": Int64(10)}],
        msg="$gt with long returns docs with value > 5",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$gt": Decimal128("5")}},
        doc=[
            {"_id": 1, "a": Decimal128("1")},
            {"_id": 2, "a": Decimal128("5")},
            {"_id": 3, "a": Decimal128("10")},
        ],
        expected=[{"_id": 3, "a": Decimal128("10")}],
        msg="$gt with decimal128 returns docs with value > 5",
    ),
    QueryTestCase(
        id="string",
        filter={"a": {"$gt": "banana"}},
        doc=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "banana"},
            {"_id": 3, "a": "cherry"},
        ],
        expected=[{"_id": 3, "a": "cherry"}],
        msg="$gt with string returns docs with value > 'banana'",
    ),
    QueryTestCase(
        id="date",
        filter={"a": {"$gt": datetime(2023, 1, 1, tzinfo=timezone.utc)}},
        doc=[
            {"_id": 1, "a": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2023, 1, 1, tzinfo=timezone.utc)},
            {"_id": 3, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 3, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)}],
        msg="$gt with date returns docs with later dates",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$gt": Timestamp(2000, 1)}},
        doc=[
            {"_id": 1, "a": Timestamp(1000, 1)},
            {"_id": 2, "a": Timestamp(3000, 1)},
        ],
        expected=[{"_id": 2, "a": Timestamp(3000, 1)}],
        msg="$gt with timestamp returns docs with larger timestamp",
    ),
    QueryTestCase(
        id="objectid",
        filter={"a": {"$gt": ObjectId("507f1f77bcf86cd799439012")}},
        doc=[
            {"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "a": ObjectId("507f1f77bcf86cd799439013")},
        ],
        expected=[{"_id": 2, "a": ObjectId("507f1f77bcf86cd799439013")}],
        msg="$gt with ObjectId returns docs with later ObjectId",
    ),
    QueryTestCase(
        id="boolean",
        filter={"a": {"$gt": False}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        expected=[{"_id": 2, "a": True}],
        msg="$gt with boolean false returns doc with true",
    ),
    QueryTestCase(
        id="bindata",
        filter={"a": {"$gt": Binary(b"\x05\x06", 128)}},
        doc=[
            {"_id": 1, "a": Binary(b"\x01\x02", 128)},
            {"_id": 2, "a": Binary(b"\x09\x0a", 128)},
        ],
        expected=[{"_id": 2, "a": Binary(b"\x09\x0a", 128)}],
        msg="$gt with BinData returns docs with larger binary",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$gt": MinKey()}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$gt with MinKey returns all non-MinKey docs",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$gt": MaxKey()}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": MaxKey()},
        ],
        expected=[],
        msg="$gt with MaxKey returns nothing",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_gt_bson_wiring(collection, test):
    """Parametrized test for $gt BSON type wiring."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter}, codec_options=codec
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)
