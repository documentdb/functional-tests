"""
Tests for $exists argument truthiness.

Tests non-obvious truthy/falsy behavior when non-boolean values are passed
as the $exists argument. Only covers cases where the result is surprising
or where compatible engines are likely to diverge.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_NAN,
)

DOCS = [{"_id": 1, "a": 1}, {"_id": 2, "b": 2}]
EXISTS_TRUE = [{"_id": 1, "a": 1}]
EXISTS_FALSE = [{"_id": 2, "b": 2}]

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="true_matches_docs_with_field",
        filter={"a": {"$exists": True}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: true matches documents with the field",
    ),
    QueryTestCase(
        id="false_matches_docs_without_field",
        filter={"a": {"$exists": False}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: false matches documents without the field",
    ),
    QueryTestCase(
        id="int_1_as_true",
        filter={"a": {"$exists": 1}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: 1 behaves as true",
    ),
    QueryTestCase(
        id="int_0_as_false",
        filter={"a": {"$exists": 0}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: 0 behaves as false",
    ),
    QueryTestCase(
        id="negative_int_as_true",
        filter={"a": {"$exists": -1}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: -1 behaves as true (non-zero)",
    ),
    QueryTestCase(
        id="negative_zero_double_as_false",
        filter={"a": {"$exists": DOUBLE_NEGATIVE_ZERO}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: -0.0 treated as false (zero)",
    ),
    QueryTestCase(
        id="decimal128_zero_as_false",
        filter={"a": {"$exists": DECIMAL128_ZERO}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: Decimal128('0') behaves as false",
    ),
    QueryTestCase(
        id="decimal128_negative_zero_as_false",
        filter={"a": {"$exists": DECIMAL128_NEGATIVE_ZERO}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: Decimal128('-0') treated as false (zero)",
    ),
    QueryTestCase(
        id="decimal128_infinity_as_true",
        filter={"a": {"$exists": DECIMAL128_INFINITY}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: Decimal128('Infinity') behaves as true",
    ),
    QueryTestCase(
        id="decimal128_negative_infinity_as_true",
        filter={"a": {"$exists": DECIMAL128_NEGATIVE_INFINITY}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: Decimal128('-Infinity') behaves as true",
    ),
    QueryTestCase(
        id="decimal128_trailing_zero_as_true",
        filter={"a": {"$exists": DECIMAL128_TRAILING_ZERO}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: Decimal128('1.0') behaves as true (non-zero)",
    ),
    QueryTestCase(
        id="decimal128_many_trailing_zeros_as_true",
        filter={"a": {"$exists": DECIMAL128_MANY_TRAILING_ZEROS}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: Decimal128 with many trailing zeros behaves as true (non-zero)",
    ),
    QueryTestCase(
        id="decimal128_zero_trailing_decimals_as_false",
        filter={"a": {"$exists": Decimal128("0.00")}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: Decimal128('0.00') treated as false (zero representation)",
    ),
    QueryTestCase(
        id="decimal128_zero_exponent_as_false",
        filter={"a": {"$exists": Decimal128("0E+10")}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: Decimal128('0E+10') treated as false (zero representation)",
    ),
    QueryTestCase(
        id="decimal128_nan_as_true",
        filter={"a": {"$exists": DECIMAL128_NAN}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: Decimal128('NaN') behaves as true (truthy)",
    ),
    QueryTestCase(
        id="float_nan_as_true",
        filter={"a": {"$exists": FLOAT_NAN}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: float('nan') behaves as true (truthy)",
    ),
    QueryTestCase(
        id="empty_string_as_true",
        filter={"a": {"$exists": ""}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: '' behaves as true (empty string is truthy in BSON)",
    ),
    QueryTestCase(
        id="string_false_as_true",
        filter={"a": {"$exists": "false"}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: 'false' behaves as true (non-empty string is truthy)",
    ),
    QueryTestCase(
        id="empty_array_as_true",
        filter={"a": {"$exists": []}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: [] behaves as true (truthy)",
    ),
    QueryTestCase(
        id="empty_object_as_true",
        filter={"a": {"$exists": {}}},
        doc=DOCS,
        expected=EXISTS_TRUE,
        msg="$exists: {} behaves as true (truthy)",
    ),
    QueryTestCase(
        id="null_as_false",
        filter={"a": {"$exists": None}},
        doc=DOCS,
        expected=EXISTS_FALSE,
        msg="$exists: None behaves as false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_exists_argument_handling(collection, test):
    """Parametrized test for $exists argument truthiness."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
