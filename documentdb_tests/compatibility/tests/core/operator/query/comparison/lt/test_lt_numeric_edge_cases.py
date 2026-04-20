"""
Tests for $lt numeric edge cases.

Covers all cross-type numeric comparisons (int, long, double, decimal128),
non-matching cross-type comparison, INT32 and INT64 boundary values,
float and Decimal128 NaN, infinity, negative zero, precision loss,
and Decimal128 infinity.
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
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
)

CROSS_TYPE_NUMERIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_lt_double",
        filter={"a": {"$lt": 5.5}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 6}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field < double query via type bracketing",
    ),
    QueryTestCase(
        id="double_lt_int",
        filter={"a": {"$lt": 6}},
        doc=[{"_id": 1, "a": 5.5}, {"_id": 2, "a": 6.5}],
        expected=[{"_id": 1, "a": 5.5}],
        msg="double field < int query via type bracketing",
    ),
    QueryTestCase(
        id="int_lt_long",
        filter={"a": {"$lt": Int64(10)}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 15}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field < long query",
    ),
    QueryTestCase(
        id="long_lt_int",
        filter={"a": {"$lt": 10}},
        doc=[{"_id": 1, "a": Int64(5)}, {"_id": 2, "a": Int64(15)}],
        expected=[{"_id": 1, "a": Int64(5)}],
        msg="long field < int query",
    ),
    QueryTestCase(
        id="int_lt_decimal128",
        filter={"a": {"$lt": Decimal128("10.5")}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 15}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field < decimal128 query",
    ),
    QueryTestCase(
        id="decimal128_lt_int",
        filter={"a": {"$lt": 10}},
        doc=[{"_id": 1, "a": Decimal128("5")}, {"_id": 2, "a": Decimal128("15")}],
        expected=[{"_id": 1, "a": Decimal128("5")}],
        msg="decimal128 field < int query",
    ),
    QueryTestCase(
        id="long_lt_double",
        filter={"a": {"$lt": 10.5}},
        doc=[{"_id": 1, "a": Int64(5)}, {"_id": 2, "a": Int64(15)}],
        expected=[{"_id": 1, "a": Int64(5)}],
        msg="long field < double query",
    ),
    QueryTestCase(
        id="double_lt_long",
        filter={"a": {"$lt": Int64(10)}},
        doc=[{"_id": 1, "a": 5.5}, {"_id": 2, "a": 15.5}],
        expected=[{"_id": 1, "a": 5.5}],
        msg="double field < long query",
    ),
    QueryTestCase(
        id="long_lt_decimal128",
        filter={"a": {"$lt": Decimal128("10.5")}},
        doc=[{"_id": 1, "a": Int64(5)}, {"_id": 2, "a": Int64(15)}],
        expected=[{"_id": 1, "a": Int64(5)}],
        msg="long field < decimal128 query",
    ),
    QueryTestCase(
        id="decimal128_lt_long",
        filter={"a": {"$lt": Int64(10)}},
        doc=[{"_id": 1, "a": Decimal128("5")}, {"_id": 2, "a": Decimal128("15")}],
        expected=[{"_id": 1, "a": Decimal128("5")}],
        msg="decimal128 field < long query",
    ),
    QueryTestCase(
        id="double_lt_decimal128",
        filter={"a": {"$lt": Decimal128("10.5")}},
        doc=[{"_id": 1, "a": 5.5}, {"_id": 2, "a": 15.5}],
        expected=[{"_id": 1, "a": 5.5}],
        msg="double field < decimal128 query",
    ),
    QueryTestCase(
        id="decimal128_lt_double",
        filter={"a": {"$lt": 10.5}},
        doc=[{"_id": 1, "a": Decimal128("5.5")}, {"_id": 2, "a": Decimal128("15.5")}],
        expected=[{"_id": 1, "a": Decimal128("5.5")}],
        msg="decimal128 field < double query",
    ),
]

NON_MATCHING_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_not_lt_int",
        filter={"a": {"$lt": 10}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="string field does not match $lt with int query",
    ),
]

BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="boundary_int64_max_equal",
        filter={"a": {"$lt": INT64_MAX}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[],
        msg="$lt with INT64_MAX equal value does not match",
    ),
    QueryTestCase(
        id="boundary_int64_max_less",
        filter={"a": {"$lt": INT64_MAX}},
        doc=[{"_id": 1, "a": Int64(INT64_MAX - 1)}],
        expected=[{"_id": 1, "a": Int64(INT64_MAX - 1)}],
        msg="$lt with INT64_MAX matches value one less",
    ),
    QueryTestCase(
        id="boundary_int32_max_equal",
        filter={"a": {"$lt": INT32_MAX}},
        doc=[{"_id": 1, "a": INT32_MAX}],
        expected=[],
        msg="$lt with INT32_MAX equal value does not match",
    ),
    QueryTestCase(
        id="boundary_int32_max_less",
        filter={"a": {"$lt": INT32_MAX}},
        doc=[{"_id": 1, "a": INT32_MAX - 1}],
        expected=[{"_id": 1, "a": INT32_MAX - 1}],
        msg="$lt with INT32_MAX - 1 matches",
    ),
    QueryTestCase(
        id="boundary_int32_min_equal",
        filter={"a": {"$lt": INT32_MIN}},
        doc=[{"_id": 1, "a": INT32_MIN}],
        expected=[],
        msg="$lt with INT32_MIN equal value does not match",
    ),
    QueryTestCase(
        id="boundary_int32_min_plus1",
        filter={"a": {"$lt": INT32_MIN + 1}},
        doc=[{"_id": 1, "a": INT32_MIN}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="$lt with INT32_MIN + 1 matches INT32_MIN",
    ),
    QueryTestCase(
        id="boundary_int32_max_cross_to_long",
        filter={"a": {"$lt": Int64(INT32_MAX + 1)}},
        doc=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": Int64(INT32_MAX + 2)}],
        expected=[{"_id": 1, "a": INT32_MAX}],
        msg="$lt INT32_MAX < INT32_MAX+1 (as long) cross-boundary",
    ),
]

NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_field_not_lt_number",
        filter={"a": {"$lt": 5}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="NaN field does not match $lt 5",
    ),
    QueryTestCase(
        id="number_not_lt_nan_query",
        filter={"a": {"$lt": FLOAT_NAN}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="numeric field does not match $lt NaN",
    ),
    QueryTestCase(
        id="decimal128_nan_field_not_lt_number",
        filter={"a": {"$lt": Decimal128("5")}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}],
        expected=[],
        msg="Decimal128 NaN field does not match $lt decimal128 numeric",
    ),
    QueryTestCase(
        id="decimal128_number_not_lt_decimal128_nan",
        filter={"a": {"$lt": DECIMAL128_NAN}},
        doc=[{"_id": 1, "a": Decimal128("5")}],
        expected=[],
        msg="Decimal128 numeric field does not match $lt Decimal128 NaN",
    ),
]

INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="number_lt_infinity",
        filter={"a": {"$lt": FLOAT_INFINITY}},
        doc=[{"_id": 1, "a": 999999}],
        expected=[{"_id": 1, "a": 999999}],
        msg="large number is less than Infinity",
    ),
    QueryTestCase(
        id="number_not_lt_neg_infinity",
        filter={"a": {"$lt": FLOAT_NEGATIVE_INFINITY}},
        doc=[{"_id": 1, "a": -999999}],
        expected=[],
        msg="negative number is not less than -Infinity",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="neg_zero_not_lt_pos_zero",
        filter={"a": {"$lt": 0.0}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        expected=[],
        msg="-0.0 is not less than 0.0 (they are equal)",
    ),
]

PRECISION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="long_2e53_plus1_not_lt_double_2e53",
        filter={"a": {"$lt": float(DOUBLE_MAX_SAFE_INTEGER)}},
        doc=[{"_id": 1, "a": Int64(DOUBLE_PRECISION_LOSS)}],
        expected=[],
        msg="Long(2^53+1) is not less than double(2^53) — precision loss boundary",
    ),
    QueryTestCase(
        id="int64_max_lt_double_rounded_up",
        filter={"a": {"$lt": float(INT64_MAX)}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="INT64_MAX is less than rounded-up double representation",
    ),
]

DECIMAL128_INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal128_number_lt_inf",
        filter={"a": {"$lt": DECIMAL128_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("0")}, {"_id": 2, "a": DECIMAL128_INFINITY}],
        expected=[{"_id": 1, "a": Decimal128("0")}],
        msg="Decimal128 0 is less than Decimal128 Infinity",
    ),
    QueryTestCase(
        id="decimal128_number_not_lt_neg_inf",
        filter={"a": {"$lt": DECIMAL128_NEGATIVE_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("-999999")}],
        expected=[],
        msg="Decimal128 number is not less than Decimal128 -Infinity",
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
def test_lt_numeric_edge_cases(collection, test):
    """Parametrized test for $lt numeric edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
