"""
Tests for $in query operator NaN and Infinity matching.

Covers NaN self-matching, cross-type NaN, Infinity matching,
negative zero vs positive zero, and NaN non-matching with regular numbers.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_nan_matches_double_nan",
        filter={"a": {"$in": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": FLOAT_NAN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": FLOAT_NAN}],
        msg="$in with double NaN matches double NaN field",
    ),
    QueryTestCase(
        id="decimal128_nan_matches_decimal128_nan",
        filter={"a": {"$in": [DECIMAL128_NAN]}},
        doc=[
            {"_id": 1, "a": DECIMAL128_NAN},
            {"_id": 2, "a": Decimal128("1")},
        ],
        expected=[{"_id": 1, "a": DECIMAL128_NAN}],
        msg="$in with Decimal128 NaN matches Decimal128 NaN field",
    ),
    QueryTestCase(
        id="double_nan_matches_decimal128_nan",
        filter={"a": {"$in": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": DECIMAL128_NAN}],
        msg="$in with double NaN matches Decimal128 NaN (cross-type NaN matching)",
    ),
    QueryTestCase(
        id="nan_does_not_match_regular_number",
        filter={"a": {"$in": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": -1}],
        expected=[],
        msg="$in with NaN does NOT match regular numbers",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(NAN_TESTS))
def test_in_nan(collection, test_case):
    """Parametrized test for $in NaN matching."""
    collection.insert_many(test_case.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test_case.filter},
    )
    assertSuccessNaN(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)


INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_infinity_matches",
        filter={"a": {"$in": [FLOAT_INFINITY]}},
        doc=[{"_id": 1, "a": FLOAT_INFINITY}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": FLOAT_INFINITY}],
        msg="$in with double Infinity matches double Infinity field",
    ),
    QueryTestCase(
        id="double_negative_infinity_matches",
        filter={"a": {"$in": [FLOAT_NEGATIVE_INFINITY]}},
        doc=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}],
        msg="$in with double -Infinity matches double -Infinity field",
    ),
    QueryTestCase(
        id="decimal128_infinity_matches",
        filter={"a": {"$in": [DECIMAL128_INFINITY]}},
        doc=[{"_id": 1, "a": DECIMAL128_INFINITY}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 1, "a": DECIMAL128_INFINITY}],
        msg="$in with Decimal128 Infinity matches Decimal128 Infinity field",
    ),
    QueryTestCase(
        id="decimal128_negative_infinity_matches",
        filter={"a": {"$in": [DECIMAL128_NEGATIVE_INFINITY]}},
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_INFINITY}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 1, "a": DECIMAL128_NEGATIVE_INFINITY}],
        msg="$in with Decimal128 -Infinity matches Decimal128 -Infinity field",
    ),
    QueryTestCase(
        id="infinity_does_not_match_negative_infinity",
        filter={"a": {"$in": [FLOAT_INFINITY]}},
        doc=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}],
        expected=[],
        msg="$in with Infinity does NOT match -Infinity",
    ),
    QueryTestCase(
        id="double_infinity_matches_decimal128_infinity",
        filter={"a": {"$in": [FLOAT_INFINITY]}},
        doc=[{"_id": 1, "a": DECIMAL128_INFINITY}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": DECIMAL128_INFINITY}],
        msg="$in with double Infinity matches Decimal128 Infinity (cross-type)",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_negative_zero_matches_positive_zero",
        filter={"a": {"$in": [DOUBLE_NEGATIVE_ZERO]}},
        doc=[{"_id": 1, "a": DOUBLE_ZERO}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": DOUBLE_ZERO}],
        msg="$in with double -0.0 matches double 0.0",
    ),
    QueryTestCase(
        id="double_positive_zero_matches_negative_zero",
        filter={"a": {"$in": [DOUBLE_ZERO]}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        msg="$in with double 0.0 matches double -0.0",
    ),
    QueryTestCase(
        id="decimal128_negative_zero_matches_positive_zero",
        filter={"a": {"$in": [DECIMAL128_NEGATIVE_ZERO]}},
        doc=[{"_id": 1, "a": DECIMAL128_ZERO}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 1, "a": DECIMAL128_ZERO}],
        msg="$in with Decimal128 -0 matches Decimal128 0",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(INFINITY_TESTS + NEGATIVE_ZERO_TESTS))
def test_in_infinity_and_zero(collection, test_case):
    """Parametrized test for $in Infinity and negative zero matching."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
