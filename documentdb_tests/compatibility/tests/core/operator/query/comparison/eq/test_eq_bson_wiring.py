"""
Tests for $eq BSON type wiring, numeric cross-type equivalence, type
distinction, and date boundaries.

Covers matching within each BSON type (including int32, javascript, and date),
cross-type numeric equivalence, distinct types that must NOT match (bool vs int,
string vs number, null vs empty string / zero / bool, ObjectId vs its string
form, BinData subtype), and date boundary/precision cases plus
Date-vs-Timestamp-vs-ObjectId distinctness.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_Y2K,
    DATE_YEAR_1,
    DATE_YEAR_9999,
)

BSON_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double",
        filter={"a": {"$eq": 3.14}},
        doc=[{"_id": 1, "a": 3.14}, {"_id": 2, "a": 2.71}],
        expected=[{"_id": 1, "a": 3.14}],
        msg="$eq with double",
    ),
    QueryTestCase(
        id="int64",
        filter={"a": {"$eq": Int64(9999999999)}},
        doc=[{"_id": 1, "a": Int64(9999999999)}, {"_id": 2, "a": Int64(1)}],
        expected=[{"_id": 1, "a": Int64(9999999999)}],
        msg="$eq with Int64 (long)",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$eq": Decimal128("1.5")}},
        doc=[{"_id": 1, "a": Decimal128("1.5")}, {"_id": 2, "a": Decimal128("2.5")}],
        expected=[{"_id": 1, "a": Decimal128("1.5")}],
        msg="$eq with Decimal128",
    ),
    QueryTestCase(
        id="bool_true",
        filter={"a": {"$eq": True}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        expected=[{"_id": 1, "a": True}],
        msg="$eq with bool true",
    ),
    QueryTestCase(
        id="bool_false",
        filter={"a": {"$eq": False}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        expected=[{"_id": 1, "a": False}],
        msg="$eq with bool false",
    ),
    QueryTestCase(
        id="datetime",
        filter={"a": {"$eq": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        doc=[
            {"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$eq with datetime (date)",
    ),
    QueryTestCase(
        id="binary",
        filter={"a": {"$eq": Binary(b"\x01\x02\x03")}},
        doc=[{"_id": 1, "a": Binary(b"\x01\x02\x03")}, {"_id": 2, "a": Binary(b"\x04\x05")}],
        expected=[{"_id": 1, "a": b"\x01\x02\x03"}],
        msg="$eq with Binary (binData)",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$eq": Timestamp(1234567890, 1)}},
        doc=[{"_id": 1, "a": Timestamp(1234567890, 1)}, {"_id": 2, "a": Timestamp(1, 1)}],
        expected=[{"_id": 1, "a": Timestamp(1234567890, 1)}],
        msg="$eq with Timestamp",
    ),
    QueryTestCase(
        id="int32",
        filter={"a": {"$eq": 42}},
        doc=[{"_id": 1, "a": 42}, {"_id": 2, "a": 43}],
        expected=[{"_id": 1, "a": 42}],
        msg="$eq with int32 matches same-type int32",
    ),
    QueryTestCase(
        id="javascript",
        filter={"a": {"$eq": Code("function() { return 1; }")}},
        doc=[
            {"_id": 1, "a": Code("function() { return 1; }")},
            {"_id": 2, "a": Code("function() { return 2; }")},
        ],
        expected=[{"_id": 1, "a": Code("function() { return 1; }")}],
        msg="$eq with JavaScript (Code) matches same-type javascript value",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$eq": MinKey()}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": MinKey()}],
        msg="$eq with MinKey",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$eq": MaxKey()}},
        doc=[{"_id": 1, "a": MaxKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="$eq with MaxKey",
    ),
]

NUMERIC_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_matches_long",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": Int64(1)}, {"_id": 2, "a": Int64(2)}],
        expected=[{"_id": 1, "a": Int64(1)}],
        msg="$eq int(1) matches long(1)",
    ),
    QueryTestCase(
        id="int_matches_double",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 2.0}],
        expected=[{"_id": 1, "a": 1.0}],
        msg="$eq int(1) matches double(1.0)",
    ),
    QueryTestCase(
        id="int_matches_decimal128",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="$eq int(1) matches Decimal128('1')",
    ),
    QueryTestCase(
        id="long_matches_double",
        filter={"a": {"$eq": Int64(1)}},
        doc=[{"_id": 1, "a": 1.0}, {"_id": 2, "a": 2.0}],
        expected=[{"_id": 1, "a": 1.0}],
        msg="$eq long(1) matches double(1.0)",
    ),
    QueryTestCase(
        id="double_matches_decimal128",
        filter={"a": {"$eq": 1.0}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="$eq double(1.0) matches Decimal128('1')",
    ),
    QueryTestCase(
        id="all_numeric_types_match",
        filter={"a": {"$eq": 1}},
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
        msg="$eq int(1) matches all equivalent numeric types",
    ),
]

TYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_does_not_match_zero",
        filter={"a": {"$eq": False}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": False}],
        expected=[{"_id": 2, "a": False}],
        msg="$eq false does NOT match int 0",
    ),
    QueryTestCase(
        id="zero_does_not_match_false",
        filter={"a": {"$eq": 0}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="$eq int 0 does NOT match bool false",
    ),
    QueryTestCase(
        id="true_does_not_match_one",
        filter={"a": {"$eq": True}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": True}],
        expected=[{"_id": 2, "a": True}],
        msg="$eq true does NOT match int 1",
    ),
    QueryTestCase(
        id="one_does_not_match_true",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$eq int 1 does NOT match bool true",
    ),
    QueryTestCase(
        id="empty_string_does_not_match_null",
        filter={"a": {"$eq": ""}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": ""}],
        expected=[{"_id": 2, "a": ""}],
        msg="$eq empty string does NOT match null",
    ),
    QueryTestCase(
        id="null_does_not_match_zero",
        filter={"a": {"$eq": None}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": None}],
        expected=[{"_id": 2, "a": None}],
        msg="$eq null does NOT match int 0",
    ),
    QueryTestCase(
        id="null_does_not_match_false",
        filter={"a": {"$eq": None}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": None}],
        expected=[{"_id": 2, "a": None}],
        msg="$eq null does NOT match bool false",
    ),
    QueryTestCase(
        id="string_does_not_match_objectid",
        filter={"a": {"$eq": "507f1f77bcf86cd799439011"}},
        doc=[
            {"_id": 1, "a": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "a": "507f1f77bcf86cd799439011"},
        ],
        expected=[{"_id": 2, "a": "507f1f77bcf86cd799439011"}],
        msg="$eq string does NOT match an ObjectId with the same hex value",
    ),
    QueryTestCase(
        id="number_does_not_match_numeric_string",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": "1"}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$eq int 1 does NOT match the string '1'",
    ),
    QueryTestCase(
        id="numeric_string_does_not_match_number",
        filter={"a": {"$eq": "1"}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": "1"}],
        expected=[{"_id": 2, "a": "1"}],
        msg="$eq string '1' does NOT match the int 1",
    ),
    QueryTestCase(
        id="bindata_subtype_distinct",
        filter={"a": {"$eq": Binary(b"\x01\x02\x03", 0)}},
        doc=[
            {"_id": 1, "a": Binary(b"\x01\x02\x03", 0)},
            {"_id": 2, "a": Binary(b"\x01\x02\x03", 128)},
        ],
        expected=[{"_id": 1, "a": b"\x01\x02\x03"}],
        msg="$eq BinData matches only same subtype, not identical bytes with a different subtype",
    ),
]


DATE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="date_epoch",
        filter={"a": {"$eq": DATE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_EPOCH}, {"_id": 2, "a": DATE_Y2K}],
        expected=[{"_id": 1, "a": DATE_EPOCH}],
        msg="$eq with the Unix epoch (DATE_EPOCH) matches the same instant",
    ),
    QueryTestCase(
        id="date_before_epoch",
        filter={"a": {"$eq": DATE_BEFORE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}, {"_id": 2, "a": DATE_EPOCH}],
        expected=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        msg="$eq with a pre-epoch date (negative ms since epoch) matches the same instant",
    ),
    QueryTestCase(
        id="date_year_1_boundary",
        filter={"a": {"$eq": DATE_YEAR_1}},
        doc=[{"_id": 1, "a": DATE_YEAR_1}, {"_id": 2, "a": DATE_YEAR_9999}],
        expected=[{"_id": 1, "a": DATE_YEAR_1}],
        msg="$eq matches the minimum-year (year 1) date boundary",
    ),
    QueryTestCase(
        id="date_year_9999_boundary",
        filter={"a": {"$eq": DATE_YEAR_9999}},
        doc=[{"_id": 1, "a": DATE_YEAR_9999}, {"_id": 2, "a": DATE_YEAR_1}],
        expected=[{"_id": 1, "a": DATE_YEAR_9999}],
        msg="$eq matches the maximum-year (year 9999) date boundary",
    ),
    QueryTestCase(
        id="date_millisecond_precision",
        filter={"a": {"$eq": datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)}},
        doc=[
            {"_id": 1, "a": datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2024, 1, 1, 0, 0, 0, 2000, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 1, "a": datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)}],
        msg="$eq on date is millisecond-precise: matches 1ms but not a 2ms-apart instant",
    ),
    QueryTestCase(
        id="date_does_not_match_timestamp",
        filter={"a": {"$eq": DATE_Y2K}},
        doc=[
            {"_id": 1, "a": Timestamp(int(DATE_Y2K.timestamp()), 1)},
            {"_id": 2, "a": DATE_Y2K},
        ],
        expected=[{"_id": 2, "a": DATE_Y2K}],
        msg="$eq date does NOT match a Timestamp at the same instant (distinct BSON types)",
    ),
    QueryTestCase(
        id="date_does_not_match_objectid",
        filter={"a": {"$eq": DATE_Y2K}},
        doc=[
            {"_id": 1, "a": ObjectId.from_datetime(DATE_Y2K)},
            {"_id": 2, "a": DATE_Y2K},
        ],
        expected=[{"_id": 2, "a": DATE_Y2K}],
        msg="$eq date does NOT match an ObjectId whose embedded timestamp is the same instant",
    ),
]


ALL_TESTS = BSON_TYPE_TESTS + NUMERIC_CROSS_TYPE_TESTS + TYPE_DISTINCTION_TESTS + DATE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_eq_bson_wiring(collection, test):
    """Parametrized test for $eq BSON type wiring, numeric cross-type, and type distinction."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
