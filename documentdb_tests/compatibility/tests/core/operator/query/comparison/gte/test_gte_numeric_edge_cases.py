"""
Tests for $gte numeric edge cases.

Covers cross-type numeric comparison, non-matching cross-type comparison,
INT64 and INT32 boundary values, NaN (including self-equality), infinity,
negative zero, and precision loss.
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
    DECIMAL128_NEGATIVE_INFINITY,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
)

CROSS_TYPE_NUMERIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_gte_double",
        filter={"a": {"$gte": 5.0}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 4}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field >= double query via type bracketing (equal match)",
    ),
    QueryTestCase(
        id="double_gte_int",
        filter={"a": {"$gte": 5}},
        doc=[{"_id": 1, "a": 5.0}, {"_id": 2, "a": 4.5}],
        expected=[{"_id": 1, "a": 5.0}],
        msg="double field >= int query via type bracketing (equal match)",
    ),
]

NON_MATCHING_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_field_not_gte_int_query",
        filter={"a": {"$gte": 10}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="string field does not match $gte with int query",
    ),
]

BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="boundary_int64_max_equal",
        filter={"a": {"$gte": INT64_MAX}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="$gte with INT64_MAX equal value matches",
    ),
    QueryTestCase(
        id="boundary_int64_max_greater",
        filter={"a": {"$gte": INT64_MAX - 1}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="$gte with INT64_MAX matches value one greater",
    ),
]

NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_field_not_gte_number",
        filter={"a": {"$gte": 5}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="NaN field does not match $gte 5",
    ),
    QueryTestCase(
        id="number_not_gte_nan_query",
        filter={"a": {"$gte": FLOAT_NAN}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="numeric field does not match $gte NaN",
    ),
    QueryTestCase(
        id="nan_not_gte_negative_infinity",
        filter={"a": {"$gte": FLOAT_NEGATIVE_INFINITY}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="NaN does not match $gte -Infinity (NaN < -Infinity in BSON ordering)",
    ),
]

INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="infinity_gte_number",
        filter={"a": {"$gte": 999999}},
        doc=[{"_id": 1, "a": FLOAT_INFINITY}],
        expected=[{"_id": 1, "a": FLOAT_INFINITY}],
        msg="Infinity is greater than or equal to large number",
    ),
    QueryTestCase(
        id="number_not_gte_infinity",
        filter={"a": {"$gte": FLOAT_INFINITY}},
        doc=[{"_id": 1, "a": -999999}],
        expected=[],
        msg="negative number is not greater than or equal to Infinity",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="neg_zero_gte_pos_zero",
        filter={"a": {"$gte": 0.0}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        msg="-0.0 is >= 0.0 (they are equal)",
    ),
]

PRECISION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="long_2e53_plus1_gte_double_2e53",
        filter={"a": {"$gte": float(DOUBLE_MAX_SAFE_INTEGER)}},
        doc=[{"_id": 1, "a": Int64(DOUBLE_PRECISION_LOSS)}],
        expected=[{"_id": 1, "a": Int64(DOUBLE_PRECISION_LOSS)}],
        msg="Long(2^53+1) is >= double(2^53) — precision loss boundary",
    ),
    QueryTestCase(
        id="double_rounded_up_gte_int64_max",
        filter={"a": {"$gte": INT64_MAX}},
        doc=[{"_id": 1, "a": float(INT64_MAX)}],
        expected=[{"_id": 1, "a": float(INT64_MAX)}],
        msg="Rounded-up double representation is >= INT64_MAX",
    ),
]

DECIMAL128_INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal128_number_not_gte_inf",
        filter={"a": {"$gte": DECIMAL128_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("0")}],
        expected=[],
        msg="Decimal128 0 is not >= Decimal128 Infinity",
    ),
    QueryTestCase(
        id="decimal128_number_gte_neg_inf",
        filter={"a": {"$gte": DECIMAL128_NEGATIVE_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("-999999")}],
        expected=[{"_id": 1, "a": Decimal128("-999999")}],
        msg="Decimal128 number is >= Decimal128 -Infinity",
    ),
]

INT32_BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_max_equal_match",
        filter={"a": {"$gte": INT32_MAX}},
        doc=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": INT32_MAX - 1}],
        expected=[{"_id": 1, "a": INT32_MAX}],
        msg="$gte INT32_MAX matches only equal value",
    ),
    QueryTestCase(
        id="int32_min_equal_match",
        filter={"a": {"$gte": INT32_MIN}},
        doc=[{"_id": 1, "a": INT32_MIN}, {"_id": 2, "a": INT32_MIN - 1}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="$gte INT32_MIN matches equal value, not one below",
    ),
    QueryTestCase(
        id="int32_min_plus1_greater_match",
        filter={"a": {"$gte": INT32_MIN}},
        doc=[{"_id": 1, "a": INT32_MIN_PLUS_1}],
        expected=[{"_id": 1, "a": INT32_MIN_PLUS_1}],
        msg="INT32_MIN + 1 matches $gte INT32_MIN",
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
    + INT32_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gte_numeric_edge_cases(collection, test):
    """Parametrized test for $gte numeric edge cases."""
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, ignore_doc_order=True)
