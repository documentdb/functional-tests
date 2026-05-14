"""
Tests for $type query operator with special values.

Verifies $type behavior with NaN, Infinity, -Infinity, -0.0, MinKey,
MaxKey, and Decimal128 special values.
"""

import pytest
from bson import Decimal128, MaxKey, MinKey

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

SPECIAL_DOUBLE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="infinity_is_double",
        filter={"x": {"$type": "double"}},
        doc=[{"_id": 1, "x": FLOAT_INFINITY}],
        expected=[{"_id": 1, "x": FLOAT_INFINITY}],
        msg="Infinity should be matched by $type: 'double'",
    ),
    QueryTestCase(
        id="neg_infinity_is_double",
        filter={"x": {"$type": "double"}},
        doc=[{"_id": 1, "x": FLOAT_NEGATIVE_INFINITY}],
        expected=[{"_id": 1, "x": FLOAT_NEGATIVE_INFINITY}],
        msg="-Infinity should be matched by $type: 'double'",
    ),
    QueryTestCase(
        id="neg_zero_is_double",
        filter={"x": {"$type": "double"}},
        doc=[{"_id": 1, "x": DOUBLE_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "x": DOUBLE_NEGATIVE_ZERO}],
        msg="-0.0 should be matched by $type: 'double'",
    ),
    QueryTestCase(
        id="neg_zero_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": DOUBLE_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "x": DOUBLE_NEGATIVE_ZERO}],
        msg="-0.0 should be matched by $type: 'number'",
    ),
    QueryTestCase(
        id="infinity_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": FLOAT_INFINITY}],
        expected=[{"_id": 1, "x": FLOAT_INFINITY}],
        msg="Infinity should be matched by $type: 'number'",
    ),
    QueryTestCase(
        id="neg_infinity_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": FLOAT_NEGATIVE_INFINITY}],
        expected=[{"_id": 1, "x": FLOAT_NEGATIVE_INFINITY}],
        msg="-Infinity should be matched by $type: 'number'",
    ),
]


SPECIAL_DECIMAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal_nan_is_decimal",
        filter={"x": {"$type": "decimal"}},
        doc=[{"_id": 1, "x": Decimal128("NaN")}],
        expected=[{"_id": 1, "x": Decimal128("NaN")}],
        msg="Decimal128('NaN') should be matched by $type: 'decimal'",
    ),
    QueryTestCase(
        id="decimal_infinity_is_decimal",
        filter={"x": {"$type": "decimal"}},
        doc=[{"_id": 1, "x": Decimal128("Infinity")}],
        expected=[{"_id": 1, "x": Decimal128("Infinity")}],
        msg="Decimal128('Infinity') should be matched by $type: 'decimal'",
    ),
    QueryTestCase(
        id="decimal_neg_infinity_is_decimal",
        filter={"x": {"$type": "decimal"}},
        doc=[{"_id": 1, "x": Decimal128("-Infinity")}],
        expected=[{"_id": 1, "x": Decimal128("-Infinity")}],
        msg="Decimal128('-Infinity') should be matched by $type: 'decimal'",
    ),
    QueryTestCase(
        id="decimal_nan_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": Decimal128("NaN")}],
        expected=[{"_id": 1, "x": Decimal128("NaN")}],
        msg="Decimal128('NaN') should be matched by $type: 'number'",
    ),
    QueryTestCase(
        id="decimal_infinity_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": Decimal128("Infinity")}],
        expected=[{"_id": 1, "x": Decimal128("Infinity")}],
        msg="Decimal128('Infinity') should be matched by $type: 'number'",
    ),
    QueryTestCase(
        id="decimal_neg_infinity_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": Decimal128("-Infinity")}],
        expected=[{"_id": 1, "x": Decimal128("-Infinity")}],
        msg="Decimal128('-Infinity') should be matched by $type: 'number'",
    ),
    QueryTestCase(
        id="decimal_neg_zero_is_decimal",
        filter={"x": {"$type": "decimal"}},
        doc=[{"_id": 1, "x": Decimal128("-0")}],
        expected=[{"_id": 1, "x": Decimal128("-0")}],
        msg="Decimal128('-0') should be matched by $type: 'decimal'",
    ),
    QueryTestCase(
        id="decimal_neg_zero_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": Decimal128("-0")}],
        expected=[{"_id": 1, "x": Decimal128("-0")}],
        msg="Decimal128('-0') should be matched by $type: 'number'",
    ),
]

MINKEY_MAXKEY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="minkey_matches_minkey_field",
        filter={"x": {"$type": "minKey"}},
        doc=[{"_id": 1, "x": MinKey()}, {"_id": 2, "x": None}],
        expected=[{"_id": 1, "x": MinKey()}],
        msg="$type: 'minKey' should only match MinKey values",
    ),
    QueryTestCase(
        id="maxkey_matches_maxkey_field",
        filter={"x": {"$type": "maxKey"}},
        doc=[{"_id": 1, "x": MaxKey()}, {"_id": 2, "x": FLOAT_INFINITY}],
        expected=[{"_id": 1, "x": MaxKey()}],
        msg="$type: 'maxKey' should only match MaxKey values",
    ),
    QueryTestCase(
        id="minkey_not_match_null",
        filter={"x": {"$type": "minKey"}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "x": 0}, {"_id": 3, "x": ""}],
        expected=[],
        msg="$type: 'minKey' should NOT match null, 0, or empty string",
    ),
    QueryTestCase(
        id="maxkey_not_match_infinity",
        filter={"x": {"$type": "maxKey"}},
        doc=[{"_id": 1, "x": FLOAT_INFINITY}],
        expected=[],
        msg="$type: 'maxKey' should NOT match Infinity",
    ),
]

ALL_TESTS = SPECIAL_DOUBLE_TESTS + SPECIAL_DECIMAL_TESTS + MINKEY_MAXKEY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_type_special_values(collection, test):
    """Test $type with special numeric values, MinKey, and MaxKey."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_is_double",
        filter={"x": {"$type": "double"}},
        doc=[{"_id": 1, "x": FLOAT_NAN}],
        expected=[{"_id": 1, "x": FLOAT_NAN}],
        msg="NaN should be matched by $type: 'double'",
    ),
    QueryTestCase(
        id="nan_is_number",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": FLOAT_NAN}],
        expected=[{"_id": 1, "x": FLOAT_NAN}],
        msg="NaN should be matched by $type: 'number'",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_TESTS))
def test_type_nan_values(collection, test):
    """Test $type with NaN values (requires NaN-aware comparison)."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccessNaN(result, test.expected, ignore_doc_order=True, msg=test.msg)
