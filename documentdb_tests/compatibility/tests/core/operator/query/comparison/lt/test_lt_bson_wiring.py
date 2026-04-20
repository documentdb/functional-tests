"""
Tests for $lt BSON type wiring.

A representative sample of types to confirm $lt is wired up to the
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
        filter={"a": {"$lt": 7.0}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 5.0}, {"_id": 3, "a": 10.0}],
        expected=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 5.0}],
        msg="$lt with double returns docs with value < 7.0",
    ),
    QueryTestCase(
        id="int",
        filter={"a": {"$lt": 7}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 10}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 5}],
        msg="$lt with int returns docs with value < 7",
    ),
    QueryTestCase(
        id="long",
        filter={"a": {"$lt": Int64(7)}},
        doc=[
            {"_id": 1, "a": Int64(1)},
            {"_id": 2, "a": Int64(5)},
            {"_id": 3, "a": Int64(10)},
        ],
        expected=[{"_id": 1, "a": Int64(1)}, {"_id": 2, "a": Int64(5)}],
        msg="$lt with long returns docs with value < 7",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$lt": Decimal128("7")}},
        doc=[
            {"_id": 1, "a": Decimal128("1")},
            {"_id": 2, "a": Decimal128("5")},
            {"_id": 3, "a": Decimal128("10")},
        ],
        expected=[
            {"_id": 1, "a": Decimal128("1")},
            {"_id": 2, "a": Decimal128("5")},
        ],
        msg="$lt with decimal128 returns docs with value < 7",
    ),
    QueryTestCase(
        id="string",
        filter={"a": {"$lt": "cherry"}},
        doc=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "banana"},
            {"_id": 3, "a": "cherry"},
        ],
        expected=[{"_id": 1, "a": "apple"}, {"_id": 2, "a": "banana"}],
        msg="$lt with string returns docs with value < 'cherry'",
    ),
    QueryTestCase(
        id="date",
        filter={"a": {"$lt": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        doc=[
            {"_id": 1, "a": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2023, 1, 1, tzinfo=timezone.utc)},
            {"_id": 3, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[
            {"_id": 1, "a": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        ],
        msg="$lt with date returns docs with earlier dates",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$lt": Timestamp(2000, 1)}},
        doc=[
            {"_id": 1, "a": Timestamp(1000, 1)},
            {"_id": 2, "a": Timestamp(3000, 1)},
        ],
        expected=[{"_id": 1, "a": Timestamp(1000, 1)}],
        msg="$lt with timestamp returns docs with smaller timestamp",
    ),
    QueryTestCase(
        id="objectid",
        filter={"a": {"$lt": ObjectId("507f1f77bcf86cd799439012")}},
        doc=[
            {"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "a": ObjectId("507f1f77bcf86cd799439013")},
        ],
        expected=[{"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$lt with ObjectId returns docs with earlier ObjectId",
    ),
    QueryTestCase(
        id="boolean",
        filter={"a": {"$lt": True}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        expected=[{"_id": 1, "a": False}],
        msg="$lt with boolean true returns doc with false",
    ),
    QueryTestCase(
        id="bindata",
        filter={"a": {"$lt": Binary(b"\x05\x06", 1)}},
        doc=[
            {"_id": 1, "a": Binary(b"\x01\x02", 1)},
            {"_id": 2, "a": Binary(b"\x09\x0a", 1)},
        ],
        expected=[{"_id": 1, "a": Binary(b"\x01\x02", 1)}],
        msg="$lt with BinData returns docs with smaller binary",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$lt": MinKey()}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 1}],
        expected=[],
        msg="$lt with MinKey returns no matches",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$lt": MaxKey()}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": MaxKey()},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": "hello"}],
        msg="$lt with MaxKey returns all non-MaxKey typed docs",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_lt_bson_wiring(collection, test):
    """Parametrized test for $lt BSON type wiring."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter}, codec_options=codec
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)
