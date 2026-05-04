"""
Tests for $nin BSON type wiring, numeric cross-type equivalence, and type distinction.

Covers all major BSON types, verifies that numerically equivalent values across
int/long/double/Decimal128 are excluded by $nin, and confirms that distinct BSON types
(bool vs int, null vs empty string) do NOT incorrectly exclude.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BSON_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string",
        filter={"a": {"$nin": ["hello"]}},
        doc=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": "world"}],
        expected=[{"_id": 2, "a": "world"}],
        msg="$nin with string excludes matching document",
    ),
    QueryTestCase(
        id="double",
        filter={"a": {"$nin": [3.14]}},
        doc=[{"_id": 1, "a": 3.14}, {"_id": 2, "a": 2.71}],
        expected=[{"_id": 2, "a": 2.71}],
        msg="$nin with double excludes matching document",
    ),
    QueryTestCase(
        id="int32",
        filter={"a": {"$nin": [42]}},
        doc=[{"_id": 1, "a": 42}, {"_id": 2, "a": 99}],
        expected=[{"_id": 2, "a": 99}],
        msg="$nin with int32 excludes matching document",
    ),
    QueryTestCase(
        id="int64",
        filter={"a": {"$nin": [Int64(9999999999)]}},
        doc=[{"_id": 1, "a": Int64(9999999999)}, {"_id": 2, "a": Int64(1)}],
        expected=[{"_id": 2, "a": Int64(1)}],
        msg="$nin with Int64 excludes matching document",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$nin": [Decimal128("1.5")]}},
        doc=[{"_id": 1, "a": Decimal128("1.5")}, {"_id": 2, "a": Decimal128("2.5")}],
        expected=[{"_id": 2, "a": Decimal128("2.5")}],
        msg="$nin with Decimal128 excludes matching document",
    ),
    QueryTestCase(
        id="bool_true",
        filter={"a": {"$nin": [True]}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        expected=[{"_id": 2, "a": False}],
        msg="$nin with bool true excludes matching document",
    ),
    QueryTestCase(
        id="bool_false",
        filter={"a": {"$nin": [False]}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        expected=[{"_id": 2, "a": True}],
        msg="$nin with bool false excludes matching document",
    ),
    QueryTestCase(
        id="datetime",
        filter={"a": {"$nin": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}},
        doc=[
            {"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 2, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)}],
        msg="$nin with datetime excludes matching document",
    ),
    QueryTestCase(
        id="objectid",
        filter={"a": {"$nin": [ObjectId("507f1f77bcf86cd799439011")]}},
        doc=[
            {"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "a": ObjectId("507f1f77bcf86cd799439012")},
        ],
        expected=[{"_id": 2, "a": ObjectId("507f1f77bcf86cd799439012")}],
        msg="$nin with ObjectId excludes matching document",
    ),
    QueryTestCase(
        id="embedded_document",
        filter={"a": {"$nin": [{"x": 1, "y": 2}]}},
        doc=[{"_id": 1, "a": {"x": 1, "y": 2}}, {"_id": 2, "a": {"x": 3}}],
        expected=[{"_id": 2, "a": {"x": 3}}],
        msg="$nin with embedded document excludes matching document",
    ),
    QueryTestCase(
        id="array",
        filter={"a": {"$nin": [[1, 2, 3]]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [4, 5]}],
        expected=[{"_id": 2, "a": [4, 5]}],
        msg="$nin with array excludes matching document",
    ),
    QueryTestCase(
        id="null",
        filter={"a": {"$nin": [None]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with null excludes matching document",
    ),
    QueryTestCase(
        id="regex",
        filter={"a": {"$nin": [Regex("^hello")]}},
        doc=[{"_id": 1, "a": "hello world"}, {"_id": 2, "a": "goodbye"}],
        expected=[{"_id": 2, "a": "goodbye"}],
        msg="$nin with regex excludes matching document",
    ),
    QueryTestCase(
        id="binary",
        filter={"a": {"$nin": [Binary(b"\x01\x02\x03")]}},
        doc=[{"_id": 1, "a": Binary(b"\x01\x02\x03")}, {"_id": 2, "a": Binary(b"\x04\x05")}],
        expected=[{"_id": 2, "a": b"\x04\x05"}],
        msg="$nin with Binary excludes matching document",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$nin": [Timestamp(1234567890, 1)]}},
        doc=[{"_id": 1, "a": Timestamp(1234567890, 1)}, {"_id": 2, "a": Timestamp(1, 1)}],
        expected=[{"_id": 2, "a": Timestamp(1, 1)}],
        msg="$nin with Timestamp excludes matching document",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$nin": [MinKey()]}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with MinKey excludes matching document",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$nin": [MaxKey()]}},
        doc=[{"_id": 1, "a": MaxKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with MaxKey excludes matching document",
    ),
]

NUMERIC_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_excludes_long",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": Int64(1)}, {"_id": 2, "a": Int64(2)}],
        expected=[{"_id": 2, "a": Int64(2)}],
        msg="$nin int(1) excludes long(1)",
    ),
    QueryTestCase(
        id="int_excludes_double",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 2.0}],
        expected=[{"_id": 2, "a": 2.0}],
        msg="$nin int(1) excludes double(1.0)",
    ),
    QueryTestCase(
        id="int_excludes_decimal128",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 2, "a": Decimal128("2")}],
        msg="$nin int(1) excludes Decimal128('1')",
    ),
    QueryTestCase(
        id="long_excludes_double",
        filter={"a": {"$nin": [Int64(1)]}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 2.0}],
        expected=[{"_id": 2, "a": 2.0}],
        msg="$nin long(1) excludes double(1.0)",
    ),
    QueryTestCase(
        id="double_excludes_decimal128",
        filter={"a": {"$nin": [1.0]}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 2, "a": Decimal128("2")}],
        msg="$nin double(1.0) excludes Decimal128('1')",
    ),
    QueryTestCase(
        id="all_numeric_types_excluded",
        filter={"a": {"$nin": [1]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": Int64(1)},
            {"_id": 3, "a": 1.0},
            {"_id": 4, "a": Decimal128("1")},
            {"_id": 5, "a": 2},
        ],
        expected=[{"_id": 5, "a": 2}],
        msg="$nin int(1) excludes all equivalent numeric types",
    ),
]

TYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_does_not_exclude_zero",
        filter={"a": {"$nin": [False]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": False}],
        expected=[{"_id": 1, "a": 0}],
        msg="$nin false does NOT exclude int 0",
    ),
    QueryTestCase(
        id="zero_does_not_exclude_false",
        filter={"a": {"$nin": [0]}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": False}],
        msg="$nin int 0 does NOT exclude bool false",
    ),
    QueryTestCase(
        id="true_does_not_exclude_one",
        filter={"a": {"$nin": [True]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": True}],
        expected=[{"_id": 1, "a": 1}],
        msg="$nin true does NOT exclude int 1",
    ),
    QueryTestCase(
        id="one_does_not_exclude_true",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": True}],
        msg="$nin int 1 does NOT exclude bool true",
    ),
    QueryTestCase(
        id="type_null_does_not_exclude_empty_string",
        filter={"a": {"$nin": [None]}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": None}],
        expected=[{"_id": 1, "a": ""}],
        msg="$nin null does NOT exclude empty string",
    ),
    QueryTestCase(
        id="empty_string_does_not_exclude_null",
        filter={"a": {"$nin": [""]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": ""}],
        expected=[{"_id": 1, "a": None}],
        msg="$nin empty string does NOT exclude null",
    ),
    QueryTestCase(
        id="null_does_not_exclude_zero",
        filter={"a": {"$nin": [None]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": None}],
        expected=[{"_id": 1, "a": 0}],
        msg="$nin null does NOT exclude int 0",
    ),
    QueryTestCase(
        id="null_does_not_exclude_false",
        filter={"a": {"$nin": [None]}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": None}],
        expected=[{"_id": 1, "a": False}],
        msg="$nin null does NOT exclude bool false",
    ),
    QueryTestCase(
        id="datetime_does_not_exclude_timestamp",
        filter={"a": {"$nin": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}},
        doc=[
            {"_id": 1, "a": Timestamp(1704067200, 0)},
            {"_id": 2, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 1, "a": Timestamp(1704067200, 0)}],
        msg="$nin datetime does NOT exclude Timestamp with same epoch seconds",
    ),
]

TESTS = BSON_TYPE_TESTS + NUMERIC_CROSS_TYPE_TESTS + TYPE_DISTINCTION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_nin_bson_wiring(collection, test_case):
    """Parametrized test for $nin BSON type wiring."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
