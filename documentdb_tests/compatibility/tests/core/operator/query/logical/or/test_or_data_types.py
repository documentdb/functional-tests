"""
Tests for $or data type coverage and BSON type distinction.

Tests that $or correctly matches documents with various BSON types
(including Regex, MinKey, MaxKey, Code), respects type distinctions
(e.g., bool vs int, null vs missing, 0.0 vs -0.0), and handles
special values (Infinity, NaN).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32",
        filter={"$or": [{"val": 42}]},
        doc=[{"_id": 1, "val": 42}, {"_id": 2, "val": 99}],
        expected=[{"_id": 1, "val": 42}],
        msg="$or matches int32 value",
    ),
    QueryTestCase(
        id="int64",
        filter={"$or": [{"val": Int64(123456789012345)}]},
        doc=[{"_id": 1, "val": Int64(123456789012345)}, {"_id": 2, "val": 0}],
        expected=[{"_id": 1, "val": Int64(123456789012345)}],
        msg="$or matches int64 value",
    ),
    QueryTestCase(
        id="double",
        filter={"$or": [{"val": 3.14}]},
        doc=[{"_id": 1, "val": 3.14}, {"_id": 2, "val": 2.71}],
        expected=[{"_id": 1, "val": 3.14}],
        msg="$or matches double value",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"$or": [{"val": Decimal128("1.23")}]},
        doc=[{"_id": 1, "val": Decimal128("1.23")}, {"_id": 2, "val": Decimal128("4.56")}],
        expected=[{"_id": 1, "val": Decimal128("1.23")}],
        msg="$or matches decimal128 value",
    ),
    QueryTestCase(
        id="string",
        filter={"$or": [{"val": "hello"}]},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": "world"}],
        expected=[{"_id": 1, "val": "hello"}],
        msg="$or matches string value",
    ),
    QueryTestCase(
        id="bool_true",
        filter={"$or": [{"val": True}]},
        doc=[{"_id": 1, "val": True}, {"_id": 2, "val": False}],
        expected=[{"_id": 1, "val": True}],
        msg="$or matches boolean true",
    ),
    QueryTestCase(
        id="bool_false",
        filter={"$or": [{"val": False}]},
        doc=[{"_id": 1, "val": True}, {"_id": 2, "val": False}],
        expected=[{"_id": 2, "val": False}],
        msg="$or matches boolean false",
    ),
    QueryTestCase(
        id="date",
        filter={"$or": [{"val": datetime(2024, 1, 1, tzinfo=timezone.utc)}]},
        doc=[
            {"_id": 1, "val": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "val": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 1, "val": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$or matches date value",
    ),
    QueryTestCase(
        id="null",
        filter={"$or": [{"val": None}]},
        doc=[{"_id": 1, "val": None}, {"_id": 2, "val": 1}],
        expected=[{"_id": 1, "val": None}],
        msg="$or matches null value",
    ),
    QueryTestCase(
        id="object",
        filter={"$or": [{"val": {"x": 1}}]},
        doc=[{"_id": 1, "val": {"x": 1}}, {"_id": 2, "val": {"x": 2}}],
        expected=[{"_id": 1, "val": {"x": 1}}],
        msg="$or matches embedded object",
    ),
    QueryTestCase(
        id="array",
        filter={"$or": [{"val": [1, 2, 3]}]},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": [4, 5]}],
        expected=[{"_id": 1, "val": [1, 2, 3]}],
        msg="$or matches array value",
    ),
    QueryTestCase(
        id="objectid",
        filter={"$or": [{"val": ObjectId("507f1f77bcf86cd799439011")}]},
        doc=[
            {"_id": 1, "val": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "val": ObjectId("507f1f77bcf86cd799439012")},
        ],
        expected=[{"_id": 1, "val": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$or matches ObjectId value",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"$or": [{"val": Timestamp(1, 1)}]},
        doc=[{"_id": 1, "val": Timestamp(1, 1)}, {"_id": 2, "val": Timestamp(2, 1)}],
        expected=[{"_id": 1, "val": Timestamp(1, 1)}],
        msg="$or matches Timestamp value",
    ),
    QueryTestCase(
        id="binary",
        filter={"$or": [{"val": Binary(b"\x01\x02")}]},
        doc=[{"_id": 1, "val": Binary(b"\x01\x02")}, {"_id": 2, "val": Binary(b"\x03")}],
        expected=[{"_id": 1, "val": b"\x01\x02"}],
        msg="$or matches Binary value",
    ),
    QueryTestCase(
        id="regex",
        filter={"$or": [{"val": Regex("^hello")}]},
        doc=[{"_id": 1, "val": "hello world"}, {"_id": 2, "val": "world"}],
        expected=[{"_id": 1, "val": "hello world"}],
        msg="$or matches Regex value",
    ),
    QueryTestCase(
        id="minkey",
        filter={"$or": [{"val": MinKey()}]},
        doc=[{"_id": 1, "val": MinKey()}, {"_id": 2, "val": 1}],
        expected=[{"_id": 1, "val": MinKey()}],
        msg="$or matches MinKey value",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"$or": [{"val": MaxKey()}]},
        doc=[{"_id": 1, "val": MaxKey()}, {"_id": 2, "val": 1}],
        expected=[{"_id": 1, "val": MaxKey()}],
        msg="$or matches MaxKey value",
    ),
    QueryTestCase(
        id="javascript_code",
        filter={"$or": [{"val": Code("function() { return true; }")}]},
        doc=[
            {"_id": 1, "val": Code("function() { return true; }")},
            {"_id": 2, "val": Code("function() { return false; }")},
        ],
        expected=[{"_id": 1, "val": Code("function() { return true; }")}],
        msg="$or matches JavaScript Code value",
    ),
]


BSON_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_not_zero",
        filter={"$or": [{"val": False}]},
        doc=[{"_id": 1, "val": 0}],
        expected=[],
        msg="bool false does not match int 0",
    ),
    QueryTestCase(
        id="zero_not_false",
        filter={"$or": [{"val": 0}]},
        doc=[{"_id": 1, "val": False}],
        expected=[],
        msg="int 0 does not match bool false",
    ),
    QueryTestCase(
        id="true_not_one",
        filter={"$or": [{"val": True}]},
        doc=[{"_id": 1, "val": 1}],
        expected=[],
        msg="bool true does not match int 1",
    ),
    QueryTestCase(
        id="empty_string_not_null",
        filter={"$or": [{"val": ""}]},
        doc=[{"_id": 1, "val": None}],
        expected=[],
        msg="empty string does not match null",
    ),
    QueryTestCase(
        id="numeric_equivalence_int_long",
        filter={"$or": [{"val": 1}]},
        doc=[{"_id": 1, "val": Int64(1)}],
        expected=[{"_id": 1, "val": Int64(1)}],
        msg="int 1 matches long 1 (numeric equivalence)",
    ),
    QueryTestCase(
        id="numeric_equivalence_int_double",
        filter={"$or": [{"val": 1.0}]},
        doc=[{"_id": 1, "val": 1}],
        expected=[{"_id": 1, "val": 1}],
        msg="double 1.0 matches int 1 (numeric equivalence)",
    ),
    QueryTestCase(
        id="numeric_equivalence_int_decimal128",
        filter={"$or": [{"val": Decimal128("1")}]},
        doc=[{"_id": 1, "val": 1}],
        expected=[{"_id": 1, "val": 1}],
        msg="Decimal128('1') matches int 1 (numeric equivalence)",
    ),
    QueryTestCase(
        id="null_matches_missing",
        filter={"$or": [{"val": None}]},
        doc=[{"_id": 1}],
        expected=[{"_id": 1}],
        msg="null query matches document with missing field",
    ),
    QueryTestCase(
        id="null_no_match_non_null",
        filter={"$or": [{"val": None}]},
        doc=[{"_id": 1, "val": 1}],
        expected=[],
        msg="null query does not match non-null field",
    ),
    QueryTestCase(
        id="positive_zero_matches_negative_zero",
        filter={"$or": [{"val": 0.0}]},
        doc=[{"_id": 1, "val": -0.0}],
        expected=[{"_id": 1, "val": -0.0}],
        msg="0.0 matches -0.0 (numeric equivalence)",
    ),
    QueryTestCase(
        id="negative_zero_matches_positive_zero",
        filter={"$or": [{"val": -0.0}]},
        doc=[{"_id": 1, "val": 0.0}],
        expected=[{"_id": 1, "val": 0.0}],
        msg="-0.0 matches 0.0 (numeric equivalence)",
    ),
    QueryTestCase(
        id="negative_zero_matches_int_zero",
        filter={"$or": [{"val": -0.0}]},
        doc=[{"_id": 1, "val": 0}],
        expected=[{"_id": 1, "val": 0}],
        msg="-0.0 matches int 0 (numeric equivalence)",
    ),
]


SPECIAL_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="float_infinity",
        filter={"$or": [{"val": FLOAT_INFINITY}]},
        doc=[{"_id": 1, "val": FLOAT_INFINITY}, {"_id": 2, "val": 1.0}],
        expected=[{"_id": 1, "val": FLOAT_INFINITY}],
        msg="$or matches float Infinity",
    ),
    QueryTestCase(
        id="float_neg_infinity",
        filter={"$or": [{"val": FLOAT_NEGATIVE_INFINITY}]},
        doc=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}, {"_id": 2, "val": 1.0}],
        expected=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}],
        msg="$or matches float -Infinity",
    ),
    QueryTestCase(
        id="decimal128_infinity",
        filter={"$or": [{"val": DECIMAL128_INFINITY}]},
        doc=[
            {"_id": 1, "val": DECIMAL128_INFINITY},
            {"_id": 2, "val": Decimal128("1")},
        ],
        expected=[{"_id": 1, "val": DECIMAL128_INFINITY}],
        msg="$or matches Decimal128 Infinity",
    ),
    QueryTestCase(
        id="cross_type_infinity",
        filter={"$or": [{"val": FLOAT_INFINITY}]},
        doc=[{"_id": 1, "val": DECIMAL128_INFINITY}, {"_id": 2, "val": 1.0}],
        expected=[{"_id": 1, "val": DECIMAL128_INFINITY}],
        msg="Float Infinity matches Decimal128 Infinity (numeric equivalence)",
    ),
]


ALL_TESTS = TYPE_TESTS + BSON_DISTINCTION_TESTS + SPECIAL_VALUE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_or_data_types(collection, test):
    """Test $or data type coverage, BSON type distinctions, and special values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="float_nan",
        filter={"$or": [{"val": FLOAT_NAN}]},
        doc=[{"_id": 1, "val": FLOAT_NAN}, {"_id": 2, "val": 1.0}],
        expected=[{"_id": 1, "val": FLOAT_NAN}],
        msg="$or matches float NaN",
    ),
    QueryTestCase(
        id="decimal128_nan",
        filter={"$or": [{"val": DECIMAL128_NAN}]},
        doc=[{"_id": 1, "val": DECIMAL128_NAN}, {"_id": 2, "val": Decimal128("1")}],
        expected=[{"_id": 1, "val": DECIMAL128_NAN}],
        msg="$or matches Decimal128 NaN",
    ),
    QueryTestCase(
        id="cross_type_nan",
        filter={"$or": [{"val": FLOAT_NAN}]},
        doc=[{"_id": 1, "val": DECIMAL128_NAN}, {"_id": 2, "val": 1.0}],
        expected=[{"_id": 1, "val": DECIMAL128_NAN}],
        msg="Float NaN matches Decimal128 NaN",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_TESTS))
def test_or_nan_values(collection, test):
    """Test $or with NaN values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccessNaN(result, test.expected, msg=test.msg)
