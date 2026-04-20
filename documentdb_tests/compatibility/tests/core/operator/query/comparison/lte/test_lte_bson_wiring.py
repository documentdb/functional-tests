"""
Tests for $lte BSON type wiring.

A representative sample of types to confirm $lte is wired up to the
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
        filter={"a": {"$lte": 7.0}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 7.0}, {"_id": 3, "a": 10.0}],
        expected=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 7.0}],
        msg="$lte with double returns docs with value <= 7.0",
    ),
    QueryTestCase(
        id="int",
        filter={"a": {"$lte": 7}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 7}],
        msg="$lte with int returns docs with value <= 7",
    ),
    QueryTestCase(
        id="long",
        filter={"a": {"$lte": Int64(7)}},
        doc=[
            {"_id": 1, "a": Int64(1)},
            {"_id": 2, "a": Int64(7)},
            {"_id": 3, "a": Int64(10)},
        ],
        expected=[{"_id": 1, "a": Int64(1)}, {"_id": 2, "a": Int64(7)}],
        msg="$lte with long returns docs with value <= 7",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$lte": Decimal128("7")}},
        doc=[
            {"_id": 1, "a": Decimal128("1")},
            {"_id": 2, "a": Decimal128("7")},
            {"_id": 3, "a": Decimal128("10")},
        ],
        expected=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("7")}],
        msg="$lte with decimal128 returns docs with value <= 7",
    ),
    QueryTestCase(
        id="string",
        filter={"a": {"$lte": "cherry"}},
        doc=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "banana"},
            {"_id": 3, "a": "cherry"},
            {"_id": 4, "a": "date"},
        ],
        expected=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "banana"},
            {"_id": 3, "a": "cherry"},
        ],
        msg="$lte with string returns docs with value <= 'cherry'",
    ),
    QueryTestCase(
        id="date",
        filter={"a": {"$lte": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        doc=[
            {"_id": 1, "a": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 3, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[
            {"_id": 1, "a": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        msg="$lte with date returns docs with equal or earlier dates",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$lte": Timestamp(2000, 1)}},
        doc=[
            {"_id": 1, "a": Timestamp(1000, 1)},
            {"_id": 2, "a": Timestamp(2000, 1)},
            {"_id": 3, "a": Timestamp(3000, 1)},
        ],
        expected=[{"_id": 1, "a": Timestamp(1000, 1)}, {"_id": 2, "a": Timestamp(2000, 1)}],
        msg="$lte with timestamp returns docs with equal or smaller timestamp",
    ),
    QueryTestCase(
        id="objectid",
        filter={"a": {"$lte": ObjectId("507f1f77bcf86cd799439012")}},
        doc=[
            {"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "a": ObjectId("507f1f77bcf86cd799439012")},
            {"_id": 3, "a": ObjectId("507f1f77bcf86cd799439013")},
        ],
        expected=[
            {"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "a": ObjectId("507f1f77bcf86cd799439012")},
        ],
        msg="$lte with ObjectId returns docs with equal or earlier ObjectId",
    ),
    QueryTestCase(
        id="boolean",
        filter={"a": {"$lte": True}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        expected=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        msg="$lte with boolean true returns both true and false",
    ),
    QueryTestCase(
        id="bindata",
        filter={"a": {"$lte": Binary(b"\x05\x06", 128)}},
        doc=[
            {"_id": 1, "a": Binary(b"\x01\x02", 128)},
            {"_id": 2, "a": Binary(b"\x05\x06", 128)},
            {"_id": 3, "a": Binary(b"\x09\x0a", 128)},
        ],
        expected=[
            {"_id": 1, "a": Binary(b"\x01\x02", 128)},
            {"_id": 2, "a": Binary(b"\x05\x06", 128)},
        ],
        msg="$lte with BinData returns docs with equal or smaller binary",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$lte": MinKey()}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": MinKey()}],
        msg="$lte with MinKey returns only MinKey doc",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$lte": MaxKey()}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": MaxKey()},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": "hello"}, {"_id": 3, "a": MaxKey()}],
        msg="$lte with MaxKey returns all docs",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_lte_bson_wiring(collection, test):
    """Parametrized test for $lte BSON type wiring."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter}, codec_options=codec
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)
