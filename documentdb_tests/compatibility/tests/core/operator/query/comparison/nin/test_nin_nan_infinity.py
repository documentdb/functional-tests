"""
Tests for $nin query operator NaN and Infinity matching.

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
        id="double_nan_excludes_double_nan",
        filter={"a": {"$nin": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": FLOAT_NAN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with double NaN excludes double NaN field",
    ),
    QueryTestCase(
        id="decimal128_nan_excludes_decimal128_nan",
        filter={"a": {"$nin": [DECIMAL128_NAN]}},
        doc=[
            {"_id": 1, "a": DECIMAL128_NAN},
            {"_id": 2, "a": Decimal128("1")},
        ],
        expected=[{"_id": 2, "a": Decimal128("1")}],
        msg="$nin with Decimal128 NaN excludes Decimal128 NaN field",
    ),
    QueryTestCase(
        id="double_nan_excludes_decimal128_nan",
        filter={"a": {"$nin": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with double NaN excludes Decimal128 NaN (cross-type NaN matching)",
    ),
    QueryTestCase(
        id="nan_does_not_exclude_regular_number",
        filter={"a": {"$nin": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": -1}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": -1}],
        msg="$nin with NaN does NOT exclude regular numbers",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(NAN_TESTS))
def test_nin_nan(collection, test_case):
    """Parametrized test for $nin NaN matching."""
    collection.insert_many(test_case.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test_case.filter},
    )
    assertSuccessNaN(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)


INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_infinity_excluded",
        filter={"a": {"$nin": [FLOAT_INFINITY]}},
        doc=[{"_id": 1, "a": FLOAT_INFINITY}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with double Infinity excludes double Infinity field",
    ),
    QueryTestCase(
        id="double_negative_infinity_excluded",
        filter={"a": {"$nin": [FLOAT_NEGATIVE_INFINITY]}},
        doc=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with double -Infinity excludes double -Infinity field",
    ),
    QueryTestCase(
        id="decimal128_infinity_excluded",
        filter={"a": {"$nin": [DECIMAL128_INFINITY]}},
        doc=[{"_id": 1, "a": DECIMAL128_INFINITY}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 2, "a": Decimal128("1")}],
        msg="$nin with Decimal128 Infinity excludes Decimal128 Infinity field",
    ),
    QueryTestCase(
        id="decimal128_negative_infinity_excluded",
        filter={"a": {"$nin": [DECIMAL128_NEGATIVE_INFINITY]}},
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_INFINITY}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 2, "a": Decimal128("1")}],
        msg="$nin with Decimal128 -Infinity excludes Decimal128 -Infinity field",
    ),
    QueryTestCase(
        id="infinity_does_not_exclude_negative_infinity",
        filter={"a": {"$nin": [FLOAT_INFINITY]}},
        doc=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}],
        expected=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}],
        msg="$nin with Infinity does NOT exclude -Infinity",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_negative_zero_excludes_positive_zero",
        filter={"a": {"$nin": [DOUBLE_NEGATIVE_ZERO]}},
        doc=[{"_id": 1, "a": DOUBLE_ZERO}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with double -0.0 excludes double 0.0",
    ),
    QueryTestCase(
        id="double_positive_zero_excludes_negative_zero",
        filter={"a": {"$nin": [DOUBLE_ZERO]}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$nin with double 0.0 excludes double -0.0",
    ),
    QueryTestCase(
        id="decimal128_negative_zero_excludes_positive_zero",
        filter={"a": {"$nin": [DECIMAL128_NEGATIVE_ZERO]}},
        doc=[{"_id": 1, "a": DECIMAL128_ZERO}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 2, "a": Decimal128("1")}],
        msg="$nin with Decimal128 -0 excludes Decimal128 0",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(INFINITY_TESTS + NEGATIVE_ZERO_TESTS))
def test_nin_infinity_and_zero(collection, test_case):
    """Parametrized test for $nin Infinity and negative zero matching."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
