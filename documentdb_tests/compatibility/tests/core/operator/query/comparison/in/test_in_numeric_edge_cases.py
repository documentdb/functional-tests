"""
Tests for $in query operator numeric boundary and edge cases.

Covers INT32/INT64 boundaries, Decimal128 precision boundaries,
trailing zeros equivalence, and scientific notation equivalence.
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
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_max",
        filter={"a": {"$in": [INT32_MAX]}},
        doc=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT32_MAX}],
        msg="$in matches INT32_MAX",
    ),
    QueryTestCase(
        id="int32_min",
        filter={"a": {"$in": [INT32_MIN]}},
        doc=[{"_id": 1, "a": INT32_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="$in matches INT32_MIN",
    ),
    QueryTestCase(
        id="int64_max",
        filter={"a": {"$in": [INT64_MAX]}},
        doc=[{"_id": 1, "a": INT64_MAX}, {"_id": 2, "a": Int64(0)}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="$in matches INT64_MAX",
    ),
    QueryTestCase(
        id="int64_min",
        filter={"a": {"$in": [INT64_MIN]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": Int64(0)}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="$in matches INT64_MIN",
    ),
    QueryTestCase(
        id="decimal128_max",
        filter={"a": {"$in": [DECIMAL128_MAX]}},
        doc=[{"_id": 1, "a": DECIMAL128_MAX}, {"_id": 2, "a": Decimal128("0")}],
        expected=[{"_id": 1, "a": DECIMAL128_MAX}],
        msg="$in matches DECIMAL128_MAX",
    ),
    QueryTestCase(
        id="decimal128_min",
        filter={"a": {"$in": [DECIMAL128_MIN]}},
        doc=[{"_id": 1, "a": DECIMAL128_MIN}, {"_id": 2, "a": Decimal128("0")}],
        expected=[{"_id": 1, "a": DECIMAL128_MIN}],
        msg="$in matches DECIMAL128_MIN",
    ),
    QueryTestCase(
        id="decimal128_min_positive",
        filter={"a": {"$in": [DECIMAL128_MIN_POSITIVE]}},
        doc=[{"_id": 1, "a": DECIMAL128_MIN_POSITIVE}, {"_id": 2, "a": Decimal128("0")}],
        expected=[{"_id": 1, "a": DECIMAL128_MIN_POSITIVE}],
        msg="$in matches DECIMAL128_MIN_POSITIVE",
    ),
    QueryTestCase(
        id="decimal128_small_exponent",
        filter={"a": {"$in": [DECIMAL128_SMALL_EXPONENT]}},
        doc=[{"_id": 1, "a": DECIMAL128_SMALL_EXPONENT}, {"_id": 2, "a": Decimal128("0")}],
        expected=[{"_id": 1, "a": DECIMAL128_SMALL_EXPONENT}],
        msg="$in matches DECIMAL128_SMALL_EXPONENT",
    ),
    QueryTestCase(
        id="decimal128_large_exponent",
        filter={"a": {"$in": [DECIMAL128_LARGE_EXPONENT]}},
        doc=[{"_id": 1, "a": DECIMAL128_LARGE_EXPONENT}, {"_id": 2, "a": Decimal128("0")}],
        expected=[{"_id": 1, "a": DECIMAL128_LARGE_EXPONENT}],
        msg="$in matches DECIMAL128_LARGE_EXPONENT",
    ),
    QueryTestCase(
        id="decimal128_trailing_zeros_equivalence",
        filter={"a": {"$in": [DECIMAL128_TRAILING_ZERO]}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="$in with Decimal128('1.0') matches Decimal128('1') (numeric equivalence)",
    ),
    QueryTestCase(
        id="decimal128_scientific_notation_equivalence",
        filter={"a": {"$in": [Decimal128("1.0E+2")]}},
        doc=[{"_id": 1, "a": 100}, {"_id": 2, "a": 200}],
        expected=[{"_id": 1, "a": 100}],
        msg="$in with Decimal128('1.0E+2') matches int 100 (numeric equivalence)",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_in_numeric_edge_cases(collection, test_case):
    """Parametrized test for $in numeric boundary and edge cases."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
