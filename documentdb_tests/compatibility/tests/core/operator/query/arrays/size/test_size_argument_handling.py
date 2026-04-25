"""
Tests for $size valid argument handling.

Covers valid numeric argument types, boundary values,
and numeric equivalence across int, long, double, and Decimal128.
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
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT32_MAX,
    INT64_ZERO,
)

DOCS = [
    {"_id": 1, "a": []},
    {"_id": 2, "a": [1]},
    {"_id": 3, "a": [1, 2]},
    {"_id": 4, "a": [1, 2, 3]},
]

VALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_0_matches_empty",
        filter={"a": {"$size": 0}},
        doc=DOCS,
        expected=[{"_id": 1, "a": []}],
        msg="$size 0 matches empty arrays",
    ),
    QueryTestCase(
        id="int_2_matches_two_elements",
        filter={"a": {"$size": 2}},
        doc=DOCS,
        expected=[{"_id": 3, "a": [1, 2]}],
        msg="$size 2 matches two-element arrays",
    ),
    QueryTestCase(
        id="int_1000_no_match",
        filter={"a": {"$size": 1000}},
        doc=DOCS,
        expected=[],
        msg="$size 1000 valid but no match",
    ),
    QueryTestCase(
        id="int64_0_matches_empty",
        filter={"a": {"$size": INT64_ZERO}},
        doc=DOCS,
        expected=[{"_id": 1, "a": []}],
        msg="$size NumberLong(0) matches empty arrays",
    ),
    QueryTestCase(
        id="int64_2_matches_two",
        filter={"a": {"$size": Int64(2)}},
        doc=DOCS,
        expected=[{"_id": 3, "a": [1, 2]}],
        msg="$size NumberLong(2) matches two-element arrays",
    ),
    QueryTestCase(
        id="double_0_matches_empty",
        filter={"a": {"$size": DOUBLE_ZERO}},
        doc=DOCS,
        expected=[{"_id": 1, "a": []}],
        msg="$size 0.0 matches empty arrays",
    ),
    QueryTestCase(
        id="double_2_matches_two",
        filter={"a": {"$size": 2.0}},
        doc=DOCS,
        expected=[{"_id": 3, "a": [1, 2]}],
        msg="$size 2.0 (whole double) matches two-element arrays",
    ),
    QueryTestCase(
        id="negative_zero_double_matches_empty",
        filter={"a": {"$size": DOUBLE_NEGATIVE_ZERO}},
        doc=DOCS,
        expected=[{"_id": 1, "a": []}],
        msg="$size -0.0 treated as 0, matches empty arrays",
    ),
    QueryTestCase(
        id="decimal128_0_matches_empty",
        filter={"a": {"$size": DECIMAL128_ZERO}},
        doc=DOCS,
        expected=[{"_id": 1, "a": []}],
        msg="$size Decimal128('0') matches empty arrays",
    ),
    QueryTestCase(
        id="decimal128_2_matches_two",
        filter={"a": {"$size": Decimal128("2")}},
        doc=DOCS,
        expected=[{"_id": 3, "a": [1, 2]}],
        msg="$size Decimal128('2') matches two-element arrays",
    ),
    QueryTestCase(
        id="decimal128_2_0_matches_two",
        filter={"a": {"$size": Decimal128("2.0")}},
        doc=DOCS,
        expected=[{"_id": 3, "a": [1, 2]}],
        msg="$size Decimal128('2.0') accepted as integral",
    ),
    QueryTestCase(
        id="decimal128_neg_zero_matches_empty",
        filter={"a": {"$size": DECIMAL128_NEGATIVE_ZERO}},
        doc=DOCS,
        expected=[{"_id": 1, "a": []}],
        msg="$size Decimal128('-0') treated as 0, matches empty arrays",
    ),
    QueryTestCase(
        id="decimal128_exponent_notation",
        filter={"a": {"$size": Decimal128("2E+1")}},
        doc=DOCS,
        expected=[],
        msg="$size Decimal128('2E+1') accepted as integral 20, no match",
    ),
    QueryTestCase(
        id="int32_max",
        filter={"a": {"$size": INT32_MAX}},
        doc=DOCS,
        expected=[],
        msg="$size with INT32_MAX valid but no match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_ARGUMENT_TESTS))
def test_size_valid_arguments(collection, test):
    """Parametrized test for $size valid argument types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
