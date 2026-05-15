"""
Tests for $mod query operator data type coverage.

Covers numeric field types, non-numeric field types, special numeric values
(NaN, Infinity, -0.0), null/missing field handling, BSON type distinction,
and cross-type numeric field matching.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

NUMERIC_MATCH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_int",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": 6}],
        expected=[{"_id": 1, "a": 6}],
        msg="$mod should match int field",
    ),
    QueryTestCase(
        id="field_long",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Int64(9)}],
        expected=[{"_id": 1, "a": Int64(9)}],
        msg="$mod should match long field",
    ),
    QueryTestCase(
        id="field_double",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": 12.0}],
        expected=[{"_id": 1, "a": 12.0}],
        msg="$mod should match double field",
    ),
    QueryTestCase(
        id="field_decimal128",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Decimal128("15")}],
        expected=[{"_id": 1, "a": Decimal128("15")}],
        msg="$mod should match decimal128 field",
    ),
    QueryTestCase(
        id="cross_type_all_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[
            {"_id": 1, "a": 6},
            {"_id": 2, "a": Int64(9)},
            {"_id": 3, "a": 12.0},
            {"_id": 4, "a": Decimal128("15")},
        ],
        expected=[
            {"_id": 1, "a": 6},
            {"_id": 2, "a": Int64(9)},
            {"_id": 3, "a": 12.0},
            {"_id": 4, "a": Decimal128("15")},
        ],
        msg="$mod should match all numeric types",
    ),
    QueryTestCase(
        id="cross_type_remainder_1",
        filter={"a": {"$mod": [3, 1]}},
        doc=[
            {"_id": 1, "a": 7},
            {"_id": 2, "a": Int64(10)},
            {"_id": 3, "a": 13.0},
            {"_id": 4, "a": Decimal128("16")},
        ],
        expected=[
            {"_id": 1, "a": 7},
            {"_id": 2, "a": Int64(10)},
            {"_id": 3, "a": 13.0},
            {"_id": 4, "a": Decimal128("16")},
        ],
        msg="$mod should match all numeric types with remainder 1",
    ),
    QueryTestCase(
        id="double_8_0_matches_mod_4_0",
        filter={"a": {"$mod": [4, 0]}},
        doc=[{"_id": 1, "a": 8.0}],
        expected=[{"_id": 1, "a": 8.0}],
        msg="$mod [4,0] on double 8.0 should match",
    ),
    QueryTestCase(
        id="double_8_5_mod_4_0",
        filter={"a": {"$mod": [4, 0]}},
        doc=[{"_id": 1, "a": 8.5}],
        expected=[{"_id": 1, "a": 8.5}],
        msg="$mod [4,0] on double 8.5 should match (8.5 truncated to 8, 8%4=0)",
    ),
    QueryTestCase(
        id="decimal128_9_5_mod_3_0",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Decimal128("9.5")}],
        expected=[{"_id": 1, "a": Decimal128("9.5")}],
        msg="$mod [3,0] on Decimal128 9.5 should match (truncated to 9, 9%3=0)",
    ),
]


NON_NUMERIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_string",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="$mod should not match string field",
    ),
    QueryTestCase(
        id="field_date",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected=[],
        msg="$mod should not match date field",
    ),
    QueryTestCase(
        id="field_object",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": {"b": 1}}],
        expected=[],
        msg="$mod should not match object field",
    ),
    QueryTestCase(
        id="field_array_non_numeric",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": ["x", "y"]}],
        expected=[],
        msg="$mod should not match array of non-numerics",
    ),
    QueryTestCase(
        id="field_objectid",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        expected=[],
        msg="$mod should not match ObjectId field",
    ),
    QueryTestCase(
        id="field_bindata",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Binary(b"\x01")}],
        expected=[],
        msg="$mod should not match BinData field",
    ),
    QueryTestCase(
        id="field_regex",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Regex(".*")}],
        expected=[],
        msg="$mod should not match regex field",
    ),
    QueryTestCase(
        id="field_timestamp",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Timestamp(1, 1)}],
        expected=[],
        msg="$mod should not match timestamp field",
    ),
    QueryTestCase(
        id="field_minkey",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": MinKey()}],
        expected=[],
        msg="$mod should not match MinKey field",
    ),
    QueryTestCase(
        id="field_maxkey",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": MaxKey()}],
        expected=[],
        msg="$mod should not match MaxKey field",
    ),
    QueryTestCase(
        id="field_javascript",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Code("return 1")}],
        expected=[],
        msg="$mod should not match JavaScript Code field",
    ),
    QueryTestCase(
        id="field_empty_string",
        filter={"a": {"$mod": [2, 0]}},
        doc=[{"_id": 1, "a": ""}],
        expected=[],
        msg="$mod should not match empty string",
    ),
]


SPECIAL_NUMERIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_nan_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="$mod should not match NaN field",
    ),
    QueryTestCase(
        id="field_infinity_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": FLOAT_INFINITY}],
        expected=[],
        msg="$mod should not match Infinity field",
    ),
    QueryTestCase(
        id="field_neg_infinity_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}],
        expected=[],
        msg="$mod should not match -Infinity field",
    ),
    QueryTestCase(
        id="field_decimal128_nan_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}],
        expected=[],
        msg="$mod should not match Decimal128 NaN field",
    ),
    QueryTestCase(
        id="field_decimal128_infinity_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": DECIMAL128_INFINITY}],
        expected=[],
        msg="$mod should not match Decimal128 Infinity field",
    ),
    QueryTestCase(
        id="field_decimal128_neg_infinity_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_INFINITY}],
        expected=[],
        msg="$mod should not match Decimal128 -Infinity field",
    ),
    QueryTestCase(
        id="field_neg_zero_double_matches_remainder_0",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        msg="$mod on -0.0 should match remainder 0",
    ),
    QueryTestCase(
        id="field_decimal128_neg_zero_matches_remainder_0",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO}],
        msg="$mod on Decimal128 -0 should match remainder 0",
    ),
]


NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="missing_field_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "b": 6}],
        expected=[],
        msg="$mod on missing field should not match",
    ),
    QueryTestCase(
        id="mixed_present_and_missing",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": 6}, {"_id": 2, "b": 9}, {"_id": 3, "a": None}, {"_id": 4, "a": 5}],
        expected=[{"_id": 1, "a": 6}],
        msg="$mod should only match numeric docs with matching remainder",
    ),
]


BSON_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bool_false_not_numeric_0",
        filter={"a": {"$mod": [2, 0]}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="$mod should match int 0 but not bool false",
    ),
    QueryTestCase(
        id="bool_true_not_numeric_1",
        filter={"a": {"$mod": [2, 1]}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$mod should match int 1 but not bool true",
    ),
    QueryTestCase(
        id="null_not_numeric",
        filter={"a": {"$mod": [2, 0]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="$mod should match int 0 but not null",
    ),
]


LARGE_DIVIDEND_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="large_double_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": 1e308}],
        expected=[],
        msg="$mod on very large double should not match (not representable as int64)",
    ),
    QueryTestCase(
        id="large_decimal128_no_match",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Decimal128("9.999999999999999999999999999999999E+6144")}],
        expected=[],
        msg="$mod on very large Decimal128 should not match",
    ),
]

ALL_TESTS = (
    NUMERIC_MATCH_TESTS
    + NON_NUMERIC_TESTS
    + SPECIAL_NUMERIC_TESTS
    + NULL_MISSING_TESTS
    + BSON_DISTINCTION_TESTS
    + LARGE_DIVIDEND_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_mod_data_type_coverage(collection, test):
    """Parametrized test for $mod data type coverage."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
