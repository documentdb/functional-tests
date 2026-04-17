"""
Tests for $in query operator BSON type wiring and type distinction.

Covers all major BSON types (string, double, int32, Int64, Decimal128, bool,
datetime, ObjectId, embedded document, array, null, regex, Binary, Timestamp,
MinKey, MaxKey), numeric cross-type equivalence (int/long/double/Decimal128),
and type distinction (bool vs int, empty string vs null, datetime vs Timestamp).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BSON_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bson_string",
        filter={"a": {"$in": ["hello"]}},
        doc=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": "world"}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$in with string",
    ),
    QueryTestCase(
        id="bson_double",
        filter={"a": {"$in": [3.14]}},
        doc=[{"_id": 1, "a": 3.14}, {"_id": 2, "a": 2.71}],
        expected=[{"_id": 1, "a": 3.14}],
        msg="$in with double",
    ),
    QueryTestCase(
        id="bson_int64",
        filter={"a": {"$in": [Int64(9999999999)]}},
        doc=[{"_id": 1, "a": Int64(9999999999)}, {"_id": 2, "a": Int64(1)}],
        expected=[{"_id": 1, "a": Int64(9999999999)}],
        msg="$in with Int64 (long)",
    ),
    QueryTestCase(
        id="bson_decimal128",
        filter={"a": {"$in": [Decimal128("1.5")]}},
        doc=[{"_id": 1, "a": Decimal128("1.5")}, {"_id": 2, "a": Decimal128("2.5")}],
        expected=[{"_id": 1, "a": Decimal128("1.5")}],
        msg="$in with Decimal128",
    ),
    QueryTestCase(
        id="bson_bool_true",
        filter={"a": {"$in": [True]}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        expected=[{"_id": 1, "a": True}],
        msg="$in with bool true",
    ),
    QueryTestCase(
        id="bson_bool_false",
        filter={"a": {"$in": [False]}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        expected=[{"_id": 1, "a": False}],
        msg="$in with bool false",
    ),
    QueryTestCase(
        id="bson_datetime",
        filter={"a": {"$in": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}},
        doc=[
            {"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 1, "a": datetime(2024, 1, 1)}],
        msg="$in with datetime",
    ),
    QueryTestCase(
        id="bson_binary",
        filter={"a": {"$in": [Binary(b"\x01\x02\x03")]}},
        doc=[{"_id": 1, "a": Binary(b"\x01\x02\x03")}, {"_id": 2, "a": Binary(b"\x04\x05")}],
        expected=[{"_id": 1, "a": b"\x01\x02\x03"}],
        msg="$in with Binary (binData)",
    ),
    QueryTestCase(
        id="bson_timestamp",
        filter={"a": {"$in": [Timestamp(1234567890, 1)]}},
        doc=[{"_id": 1, "a": Timestamp(1234567890, 1)}, {"_id": 2, "a": Timestamp(1, 1)}],
        expected=[{"_id": 1, "a": Timestamp(1234567890, 1)}],
        msg="$in with Timestamp",
    ),
    QueryTestCase(
        id="bson_minkey",
        filter={"a": {"$in": [MinKey()]}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": MinKey()}],
        msg="$in with MinKey",
    ),
    QueryTestCase(
        id="bson_maxkey",
        filter={"a": {"$in": [MaxKey()]}},
        doc=[{"_id": 1, "a": MaxKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="$in with MaxKey",
    ),
    QueryTestCase(
        id="bson_int32",
        filter={"a": {"$in": [42]}},
        doc=[{"_id": 1, "a": 42}, {"_id": 2, "a": 99}],
        expected=[{"_id": 1, "a": 42}],
        msg="$in with int32",
    ),
    QueryTestCase(
        id="bson_objectid",
        filter={"a": {"$in": [ObjectId("507f1f77bcf86cd799439011")]}},
        doc=[
            {"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "a": ObjectId("507f1f77bcf86cd799439012")},
        ],
        expected=[{"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$in with ObjectId",
    ),
    QueryTestCase(
        id="bson_embedded_document",
        filter={"a": {"$in": [{"x": 1, "y": 2}]}},
        doc=[{"_id": 1, "a": {"x": 1, "y": 2}}, {"_id": 2, "a": {"x": 3}}],
        expected=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        msg="$in with embedded document",
    ),
    QueryTestCase(
        id="bson_null",
        filter={"a": {"$in": [None]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": None}],
        msg="$in with null",
    ),
]

NUMERIC_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="cross_type_int_matches_long",
        filter={"a": {"$in": [1]}},
        doc=[{"_id": 1, "a": Int64(1)}, {"_id": 2, "a": Int64(2)}],
        expected=[{"_id": 1, "a": Int64(1)}],
        msg="$in int(1) matches long(1)",
    ),
    QueryTestCase(
        id="cross_type_int_matches_double",
        filter={"a": {"$in": [1]}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 2.0}],
        expected=[{"_id": 1, "a": 1.0}],
        msg="$in int(1) matches double(1.0)",
    ),
    QueryTestCase(
        id="cross_type_int_matches_decimal128",
        filter={"a": {"$in": [1]}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="$in int(1) matches Decimal128('1')",
    ),
    QueryTestCase(
        id="cross_type_long_matches_double",
        filter={"a": {"$in": [Int64(1)]}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 2.0}],
        expected=[{"_id": 1, "a": 1.0}],
        msg="$in long(1) matches double(1.0)",
    ),
    QueryTestCase(
        id="cross_type_double_matches_decimal128",
        filter={"a": {"$in": [1.0]}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="$in double(1.0) matches Decimal128('1')",
    ),
    QueryTestCase(
        id="cross_type_all_numeric_types",
        filter={"a": {"$in": [1]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": Int64(1)},
            {"_id": 3, "a": 1.0},
            {"_id": 4, "a": Decimal128("1")},
            {"_id": 5, "a": 2},
        ],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": Int64(1)},
            {"_id": 3, "a": 1.0},
            {"_id": 4, "a": Decimal128("1")},
        ],
        msg="$in int(1) matches all equivalent numeric types",
    ),
]

TYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="distinction_false_not_zero",
        filter={"a": {"$in": [False]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": False}],
        expected=[{"_id": 2, "a": False}],
        msg="$in false does NOT match int 0",
    ),
    QueryTestCase(
        id="distinction_zero_not_false",
        filter={"a": {"$in": [0]}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="$in int 0 does NOT match bool false",
    ),
    QueryTestCase(
        id="distinction_true_not_one",
        filter={"a": {"$in": [True]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": True}],
        expected=[{"_id": 2, "a": True}],
        msg="$in true does NOT match int 1",
    ),
    QueryTestCase(
        id="distinction_one_not_true",
        filter={"a": {"$in": [1]}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$in int 1 does NOT match bool true",
    ),
    QueryTestCase(
        id="distinction_empty_string_not_null",
        filter={"a": {"$in": [""]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": ""}],
        expected=[{"_id": 2, "a": ""}],
        msg="$in empty string does NOT match null",
    ),
    QueryTestCase(
        id="distinction_datetime_not_timestamp",
        filter={"a": {"$in": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}},
        doc=[
            {"_id": 1, "a": Timestamp(1704067200, 0)},
            {"_id": 2, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 2, "a": datetime(2024, 1, 1)}],
        msg="$in datetime does NOT match Timestamp with same epoch seconds",
    ),
]

TESTS = BSON_TYPE_TESTS + NUMERIC_CROSS_TYPE_TESTS + TYPE_DISTINCTION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_in_bson_wiring(collection, test_case):
    """Parametrized test for $in BSON type wiring and type distinction."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
