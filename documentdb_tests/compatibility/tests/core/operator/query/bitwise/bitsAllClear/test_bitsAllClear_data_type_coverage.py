"""
Tests for $bitsAllClear data type coverage.

Validates matching behavior across valid field types (int32, int64, double, BinData)
and numeric cross-type equivalence (int32/int64/double/Decimal128).
"""

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_NEGATIVE_ZERO

VALID_FIELD_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_field_bit0_clear",
        filter={"a": {"$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": 20}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": 20}],
        msg="Int32 field with bit 0 clear matches",
    ),
    QueryTestCase(
        id="int64_field_bit0_clear",
        filter={"a": {"$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": Int64(20)}, {"_id": 2, "a": Int64(1)}],
        expected=[{"_id": 1, "a": Int64(20)}],
        msg="Int64 field with bit 0 clear matches",
    ),
    QueryTestCase(
        id="double_field_bit0_clear",
        filter={"a": {"$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": 20.0}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 1, "a": 20.0}],
        msg="Double (integer-representable) field with bit 0 clear matches",
    ),
    QueryTestCase(
        id="bindata_field_bit0_clear",
        filter={"a": {"$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": Binary(b"\x06", 128)}, {"_id": 2, "a": Binary(b"\x01", 128)}],
        expected=[{"_id": 1, "a": Binary(b"\x06", 128)}],
        msg="BinData field with bit 0 clear matches numeric bitmask",
    ),
    QueryTestCase(
        id="negative_zero_matches",
        filter={"a": {"$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        msg="Negative zero treated as integer 0, all bits clear",
    ),
]

NUMERIC_EQUIVALENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_cross_type_equivalence",
        filter={"a": {"$bitsAllClear": [0, 1]}},
        doc=[
            {"_id": 1, "a": 20},
            {"_id": 2, "a": Int64(20)},
            {"_id": 3, "a": 20.0},
            {"_id": 4, "a": Decimal128("20")},
            {"_id": 5, "a": 3},
        ],
        expected=[
            {"_id": 1, "a": 20},
            {"_id": 2, "a": Int64(20)},
            {"_id": 3, "a": 20.0},
            {"_id": 4, "a": Decimal128("20")},
        ],
        msg="Int32, Int64, Double, Decimal128 of same value produce same match result",
    ),
]

ALL_TESTS = VALID_FIELD_TYPE_TESTS + NUMERIC_EQUIVALENCE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAllClear_data_type_coverage(collection, test):
    """Test $bitsAllClear matching behavior across valid BSON field types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
