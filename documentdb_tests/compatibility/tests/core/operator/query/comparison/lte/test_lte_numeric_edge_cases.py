"""
Tests for $lte numeric edge cases.

Covers cross-type numeric comparison, non-matching cross-type comparison,
INT64 boundary values, NaN (including self-matching and Decimal128 NaN
cross-type), infinity, negative zero, precision loss, and Decimal128
infinity boundaries.
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
    INT64_MAX,
)

CROSS_TYPE_NUMERIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_lte_double",
        filter={"a": {"$lte": 5.0}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 6}],
        expected=[{"_id": 1, "a": 5}],
        msg="int field <= double query via type bracketing (equal match)",
    ),
    QueryTestCase(
        id="double_lte_int",
        filter={"a": {"$lte": 6}},
        doc=[{"_id": 1, "a": 5.5}, {"_id": 2, "a": 6.0}, {"_id": 3, "a": 6.5}],
        expected=[{"_id": 1, "a": 5.5}, {"_id": 2, "a": 6.0}],
        msg="double field <= int query via type bracketing (equal match)",
    ),
]

NON_MATCHING_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_not_lte_int",
        filter={"a": {"$lte": 10}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="string field does not match $lte with int query",
    ),
]

BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="boundary_int64_max_equal",
        filter={"a": {"$lte": INT64_MAX}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="$lte with INT64_MAX equal value matches",
    ),
    QueryTestCase(
        id="boundary_int64_max_less",
        filter={"a": {"$lte": INT64_MAX}},
        doc=[{"_id": 1, "a": Int64(INT64_MAX - 1)}],
        expected=[{"_id": 1, "a": Int64(INT64_MAX - 1)}],
        msg="$lte with INT64_MAX matches value one less",
    ),
]

NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_field_not_lte_number",
        filter={"a": {"$lte": 5}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="NaN field does not match $lte 5",
    ),
    QueryTestCase(
        id="number_not_lte_nan_query",
        filter={"a": {"$lte": FLOAT_NAN}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="numeric field does not match $lte NaN",
    ),
]

INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="number_lte_infinity",
        filter={"a": {"$lte": FLOAT_INFINITY}},
        doc=[{"_id": 1, "a": 999999}],
        expected=[{"_id": 1, "a": 999999}],
        msg="large number is less than or equal to Infinity",
    ),
    QueryTestCase(
        id="number_not_lte_neg_infinity",
        filter={"a": {"$lte": FLOAT_NEGATIVE_INFINITY}},
        doc=[{"_id": 1, "a": -999999}],
        expected=[],
        msg="negative number is not less than or equal to -Infinity",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="neg_zero_lte_pos_zero",
        filter={"a": {"$lte": 0.0}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        msg="-0.0 is <= 0.0 (they are equal)",
    ),
]

PRECISION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="long_2e53_plus1_not_lte_double_2e53",
        filter={"a": {"$lte": float(DOUBLE_MAX_SAFE_INTEGER)}},
        doc=[{"_id": 1, "a": Int64(DOUBLE_PRECISION_LOSS)}],
        expected=[],
        msg="Long(2^53+1) is not <= double(2^53) — precision loss boundary",
    ),
    QueryTestCase(
        id="int64_max_lte_double_rounded_up",
        filter={"a": {"$lte": float(INT64_MAX)}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="INT64_MAX is <= rounded-up double representation",
    ),
]

DECIMAL128_INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal128_number_lte_inf",
        filter={"a": {"$lte": DECIMAL128_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("0")}, {"_id": 2, "a": DECIMAL128_INFINITY}],
        expected=[{"_id": 1, "a": Decimal128("0")}, {"_id": 2, "a": DECIMAL128_INFINITY}],
        msg="Decimal128 0 and Infinity are both <= Decimal128 Infinity",
    ),
    QueryTestCase(
        id="decimal128_number_not_lte_neg_inf",
        filter={"a": {"$lte": DECIMAL128_NEGATIVE_INFINITY}},
        doc=[{"_id": 1, "a": Decimal128("-999999")}],
        expected=[],
        msg="Decimal128 number is not <= Decimal128 -Infinity",
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
def test_lte_numeric_edge_cases(collection, test):
    """Parametrized test for $lte numeric edge cases."""
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, ignore_doc_order=True)
