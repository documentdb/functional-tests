"""
Tests for $gt numeric edge cases.

Covers cross-type numeric comparisons (int, long, double, decimal128),
non-matching cross-type comparison, INT32/INT64 boundary values,
NaN and Decimal128 NaN, infinity, negative zero, and precision loss.
"""

import pytest
from bson import Decimal128, Int64

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
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

CROSS_TYPE_NUMERIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_field_gt_double_query",
        filter={"a": {"$gt": 4.5}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 4}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field > double query via type bracketing",
    ),
    QueryTestCase(
        id="double_field_gt_int_query",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "a": 5.5}, {"_id": 2, "a": 4.5}],
        expected=[{"_id": 1, "a": 5.5}],
        msg="double field > int query via type bracketing",
    ),
    QueryTestCase(
        id="int_field_gt_long_query",
        filter={"a": {"$gt": Int64(4)}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 3}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field > long query",
    ),
    QueryTestCase(
        id="long_field_gt_int_query",
        filter={"a": {"$gt": 4}},
        doc=[{"_id": 1, "a": Int64(5)}, {"_id": 2, "a": Int64(3)}],
        expected=[{"_id": 1, "a": Int64(5)}],
        msg="long field > int query",
    ),
    QueryTestCase(
        id="int_field_gt_decimal128_query",
        filter={"a": {"$gt": Decimal128("4")}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 3}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field > decimal128 query",
    ),
    QueryTestCase(
        id="decimal128_field_gt_int_query",
        filter={"a": {"$gt": 4}},
        doc=[{"_id": 1, "a": Decimal128("5")}, {"_id": 2, "a": Decimal128("3")}],
        expected=[{"_id": 1, "a": Decimal128("5")}],
        msg="decimal128 field > int query",
    ),
    QueryTestCase(
        id="long_field_gt_decimal128_query",
        filter={"a": {"$gt": Decimal128("4")}},
        doc=[{"_id": 1, "a": Int64(5)}, {"_id": 2, "a": Int64(3)}],
        expected=[{"_id": 1, "a": Int64(5)}],
        msg="long field > decimal128 query",
    ),
    QueryTestCase(
        id="decimal128_field_gt_long_query",
        filter={"a": {"$gt": Int64(4)}},
        doc=[{"_id": 1, "a": Decimal128("5")}, {"_id": 2, "a": Decimal128("3")}],
        expected=[{"_id": 1, "a": Decimal128("5")}],
        msg="decimal128 field > long query",
    ),
    QueryTestCase(
        id="double_field_gt_decimal128_query",
        filter={"a": {"$gt": Decimal128("4.5")}},
        doc=[{"_id": 1, "a": 5.5}, {"_id": 2, "a": 3.5}],
        expected=[{"_id": 1, "a": 5.5}],
        msg="double field > decimal128 query",
    ),
    QueryTestCase(
        id="decimal128_field_gt_double_query",
        filter={"a": {"$gt": 4.5}},
        doc=[{"_id": 1, "a": Decimal128("5.5")}, {"_id": 2, "a": Decimal128("3.5")}],
        expected=[{"_id": 1, "a": Decimal128("5.5")}],
        msg="decimal128 field > double query",
    ),
]

NON_MATCHING_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_field_not_gt_int_query",
        filter={"a": {"$gt": 10}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="string field does not match $gt with int query",
    ),
]

BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int64_max_equal_no_match",
        filter={"a": {"$gt": INT64_MAX}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[],
        msg="$gt with INT64_MAX equal value does not match",
    ),
    QueryTestCase(
        id="int64_max_gt_int64_max_minus_1",
        filter={"a": {"$gt": INT64_MAX - 1}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="$gt with INT64_MAX matches value one greater",
    ),
    QueryTestCase(
        id="int64_min_equal_no_match",
        filter={"a": {"$gt": INT64_MIN}},
        doc=[{"_id": 1, "a": INT64_MIN}],
        expected=[],
        msg="$gt with INT64_MIN equal value does not match",
    ),
    QueryTestCase(
        id="int64_min_plus1_gt_int64_min",
        filter={"a": {"$gt": INT64_MIN}},
        doc=[{"_id": 1, "a": Int64(int(INT64_MIN) + 1)}],
        expected=[{"_id": 1, "a": Int64(int(INT64_MIN) + 1)}],
        msg="INT64_MIN+1 is greater than INT64_MIN",
    ),
    QueryTestCase(
        id="int32_max_equal_no_match",
        filter={"a": {"$gt": INT32_MAX}},
        doc=[{"_id": 1, "a": INT32_MAX}],
        expected=[],
        msg="$gt with INT32_MAX equal value does not match",
    ),
    QueryTestCase(
        id="int32_max_plus1_as_long_gt_int32_max",
        filter={"a": {"$gt": INT32_MAX}},
        doc=[{"_id": 1, "a": Int64(INT32_MAX + 1)}],
        expected=[{"_id": 1, "a": Int64(INT32_MAX + 1)}],
        msg="INT32_MAX+1 (stored as long) is greater than INT32_MAX",
    ),
    QueryTestCase(
        id="int32_min_equal_no_match",
        filter={"a": {"$gt": INT32_MIN}},
        doc=[{"_id": 1, "a": INT32_MIN}],
        expected=[],
        msg="$gt with INT32_MIN equal value does not match",
    ),
    QueryTestCase(
        id="int32_min_minus1_as_long_not_gt_int32_min",
        filter={"a": {"$gt": INT32_MIN}},
        doc=[{"_id": 1, "a": Int64(INT32_MIN - 1)}],
        expected=[],
        msg="INT32_MIN-1 (stored as long) is not greater than INT32_MIN",
    ),
]

NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="float_nan_field_not_gt_number",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="NaN field does not match $gt 5",
    ),
    QueryTestCase(
        id="number_not_gt_float_nan_query",
        filter={"a": {"$gt": FLOAT_NAN}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="numeric field does not match $gt NaN",
    ),
    QueryTestCase(
        id="float_nan_not_gt_float_nan",
        filter={"a": {"$gt": FLOAT_NAN}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="NaN is not greater than NaN",
    ),
    QueryTestCase(
        id="decimal128_nan_field_not_gt_number",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}],
        expected=[],
        msg="Decimal128 NaN field does not match $gt 5",
    ),
    QueryTestCase(
        id="number_not_gt_decimal128_nan_query",
        filter={"a": {"$gt": DECIMAL128_NAN}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="numeric field does not match $gt Decimal128 NaN",
    ),
    QueryTestCase(
        id="decimal128_nan_not_gt_decimal128_nan",
        filter={"a": {"$gt": DECIMAL128_NAN}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}],
        expected=[],
        msg="Decimal128 NaN is not greater than Decimal128 NaN",
    ),
]

INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="infinity_field_gt_large_number",
        filter={"a": {"$gt": 999999}},
        doc=[{"_id": 1, "a": FLOAT_INFINITY}],
        expected=[{"_id": 1, "a": FLOAT_INFINITY}],
        msg="Infinity is greater than large number",
    ),
    QueryTestCase(
        id="number_not_gt_infinity_query",
        filter={"a": {"$gt": FLOAT_INFINITY}},
        doc=[{"_id": 1, "a": -999999}],
        expected=[],
        msg="negative number is not greater than Infinity",
    ),
    QueryTestCase(
        id="large_double_not_gt_infinity",
        filter={"a": {"$gt": FLOAT_INFINITY}},
        doc=[{"_id": 1, "a": DOUBLE_NEAR_MAX}],
        expected=[],
        msg="1e308 is not greater than Infinity",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negative_zero_not_gt_positive_zero",
        filter={"a": {"$gt": 0.0}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        expected=[],
        msg="-0.0 is not greater than 0.0 (they are equal)",
    ),
]

PRECISION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="long_2e53_plus1_gt_double_2e53",
        filter={"a": {"$gt": float(DOUBLE_MAX_SAFE_INTEGER)}},
        doc=[{"_id": 1, "a": Int64(DOUBLE_PRECISION_LOSS)}],
        expected=[{"_id": 1, "a": Int64(DOUBLE_PRECISION_LOSS)}],
        msg="Long(2^53+1) is greater than double(2^53) — precision loss boundary",
    ),
    QueryTestCase(
        id="double_rounded_up_gt_int64_max",
        filter={"a": {"$gt": INT64_MAX}},
        doc=[{"_id": 1, "a": float(INT64_MAX)}],
        expected=[{"_id": 1, "a": float(INT64_MAX)}],
        msg="Rounded-up double representation is greater than INT64_MAX",
    ),
]

DECIMAL128_INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal128_zero_not_gt_decimal128_infinity",
        filter={"a": {"$gt": DECIMAL128_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("0")}],
        expected=[],
        msg="Decimal128 0 is not greater than Decimal128 Infinity",
    ),
    QueryTestCase(
        id="decimal128_number_gt_decimal128_neg_infinity",
        filter={"a": {"$gt": DECIMAL128_NEGATIVE_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("-999999")}],
        expected=[{"_id": 1, "a": Decimal128("-999999")}],
        msg="Decimal128 number is greater than Decimal128 -Infinity",
    ),
]

ALL_TESTS = (
    CROSS_TYPE_NUMERIC_TESTS
    + NON_MATCHING_CROSS_TYPE_TESTS
    + BOUNDARY_TESTS
    + NAN_TESTS
    + INFINITY_TESTS
    + NEGATIVE_ZERO_TESTS
    + PRECISION_TESTS
    + DECIMAL128_INFINITY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gt_numeric_edge_cases(collection, test):
    """Parametrized test for $gt numeric edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
