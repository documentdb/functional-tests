"""
Tests for $eq numeric edge cases.

Covers precision-loss boundaries near 2^53, infinity matching (including
cross-type double vs Decimal128), double and Decimal128 negative-zero
equivalence, and Decimal128 precision (MAX/MIN and decimal-vs-double 0.1).
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
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    FLOAT_INFINITY,
)

PRECISION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_safe_integer_matches_only_equal_long",
        filter={"a": {"$eq": float(DOUBLE_MAX_SAFE_INTEGER)}},
        doc=[
            {"_id": 1, "a": Int64(DOUBLE_MAX_SAFE_INTEGER)},
            {"_id": 2, "a": Int64(DOUBLE_PRECISION_LOSS)},
        ],
        expected=[{"_id": 1, "a": Int64(DOUBLE_MAX_SAFE_INTEGER)}],
        msg="$eq double(2^53) matches long(2^53) but NOT long(2^53+1) — precision-aware equality",
    ),
    QueryTestCase(
        id="long_precision_loss_matched_only_by_exact_long",
        filter={"a": {"$eq": Int64(DOUBLE_PRECISION_LOSS)}},
        doc=[
            {"_id": 1, "a": float(DOUBLE_MAX_SAFE_INTEGER)},
            {"_id": 2, "a": Int64(DOUBLE_PRECISION_LOSS)},
        ],
        expected=[{"_id": 2, "a": Int64(DOUBLE_PRECISION_LOSS)}],
        msg="$eq long(2^53+1) matches the exact long, not double(2^53) which cannot represent it",
    ),
]

INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="infinity_matches_double_infinity",
        filter={"a": {"$eq": FLOAT_INFINITY}},
        doc=[
            {"_id": 1, "a": FLOAT_INFINITY},
            {"_id": 2, "a": -FLOAT_INFINITY},
            {"_id": 3, "a": 1.0},
        ],
        expected=[{"_id": 1, "a": FLOAT_INFINITY}],
        msg="$eq Infinity matches double Infinity only (not -Infinity or finite values)",
    ),
    QueryTestCase(
        id="infinity_matches_decimal_infinity_cross_type",
        filter={"a": {"$eq": FLOAT_INFINITY}},
        doc=[
            {"_id": 1, "a": DECIMAL128_INFINITY},
            {"_id": 2, "a": DECIMAL128_NEGATIVE_INFINITY},
        ],
        expected=[{"_id": 1, "a": DECIMAL128_INFINITY}],
        msg="$eq double Infinity matches Decimal128 Infinity (cross-type numeric equivalence)",
    ),
    QueryTestCase(
        id="negative_infinity_distinct_from_positive_infinity",
        filter={"a": {"$eq": -FLOAT_INFINITY}},
        doc=[
            {"_id": 1, "a": FLOAT_INFINITY},
            {"_id": 2, "a": -FLOAT_INFINITY},
        ],
        expected=[{"_id": 2, "a": -FLOAT_INFINITY}],
        msg="$eq -Infinity does NOT match +Infinity",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="positive_zero_matches_negative_zero",
        filter={"a": {"$eq": 0.0}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        msg="$eq 0.0 matches stored -0.0 (negative zero equals positive zero)",
    ),
    QueryTestCase(
        id="positive_zero_matches_decimal128_negative_zero",
        filter={"a": {"$eq": 0.0}},
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO}, {"_id": 2, "a": Int64(1)}],
        expected=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO}],
        msg="$eq 0.0 matches stored Decimal128 -0 (negative zero equals positive zero, cross-type)",
    ),
]


DECIMAL128_PRECISION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal128_max_exact_match",
        filter={"a": {"$eq": DECIMAL128_MAX}},
        doc=[{"_id": 1, "a": DECIMAL128_MAX}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 1, "a": DECIMAL128_MAX}],
        msg="$eq matches the maximum representable Decimal128 value exactly",
    ),
    QueryTestCase(
        id="decimal128_min_exact_match",
        filter={"a": {"$eq": DECIMAL128_MIN}},
        doc=[{"_id": 1, "a": DECIMAL128_MIN}, {"_id": 2, "a": Decimal128("-1")}],
        expected=[{"_id": 1, "a": DECIMAL128_MIN}],
        msg="$eq matches the minimum (most negative) representable Decimal128 value exactly",
    ),
    QueryTestCase(
        id="decimal128_point_one_distinct_from_double_point_one",
        filter={"a": {"$eq": Decimal128("0.1")}},
        doc=[{"_id": 1, "a": 0.1}, {"_id": 2, "a": Decimal128("0.1")}],
        expected=[{"_id": 2, "a": Decimal128("0.1")}],
        msg="$eq Decimal128('0.1') does NOT match double 0.1 (distinct exact values)",
    ),
]


ALL_TESTS = PRECISION_TESTS + INFINITY_TESTS + NEGATIVE_ZERO_TESTS + DECIMAL128_PRECISION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_eq_numeric_edge_cases(collection, test):
    """Parametrized test for $eq numeric edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
