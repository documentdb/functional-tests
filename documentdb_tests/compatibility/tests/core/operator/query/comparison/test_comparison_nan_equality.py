"""
Tests for NaN equality behavior across comparison query operators.

Verifies that NaN == NaN for $eq, $gte, $lte with both float and Decimal128 NaN.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

FLOAT_NAN = float("nan")
DECIMAL128_NAN = Decimal128("NaN")

NAN_EQUALITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="eq_float_nan",
        filter={"a": {"$eq": FLOAT_NAN}},
        doc=[{"_id": 1, "a": FLOAT_NAN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": FLOAT_NAN}],
        msg="$eq matches float NaN to float NaN",
    ),
    QueryTestCase(
        id="eq_decimal128_nan",
        filter={"a": {"$eq": DECIMAL128_NAN}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 1, "a": DECIMAL128_NAN}],
        msg="$eq matches Decimal128 NaN to Decimal128 NaN",
    ),
    QueryTestCase(
        id="gte_float_nan",
        filter={"a": {"$gte": FLOAT_NAN}},
        doc=[{"_id": 1, "a": FLOAT_NAN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": FLOAT_NAN}],
        msg="$gte matches float NaN to float NaN (NaN == NaN)",
    ),
    QueryTestCase(
        id="gte_decimal128_nan",
        filter={"a": {"$gte": DECIMAL128_NAN}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 1, "a": DECIMAL128_NAN}],
        msg="$gte matches Decimal128 NaN to Decimal128 NaN (NaN == NaN)",
    ),
    QueryTestCase(
        id="lte_float_nan",
        filter={"a": {"$lte": FLOAT_NAN}},
        doc=[{"_id": 1, "a": FLOAT_NAN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": FLOAT_NAN}],
        msg="$lte matches float NaN to float NaN (NaN == NaN)",
    ),
    QueryTestCase(
        id="lte_decimal128_nan",
        filter={"a": {"$lte": DECIMAL128_NAN}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 1, "a": DECIMAL128_NAN}],
        msg="$lte matches Decimal128 NaN to Decimal128 NaN (NaN == NaN)",
    ),
]


ALL_TESTS = NAN_EQUALITY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_comparison_nan_equality(collection, test):
    """Test NaN equality across $eq, $gte, $lte for float and Decimal128."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccessNaN(result, test.expected, ignore_doc_order=True)
