"""
Tests for $bitsAllSet valid argument handling.

Validates valid bitmask forms: numeric (integer, Decimal128), BinData, and position list.
"""

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_MAX

VALID_NUMERIC_BITMASK_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_bitmask_zero",
        filter={"a": {"$bitsAllSet": 0}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": -1}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": -1}],
        msg="Bitmask 0 matches all integer-representable documents",
    ),
    QueryTestCase(
        id="numeric_bitmask_35",
        filter={"a": {"$bitsAllSet": 35}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 35}, {"_id": 3, "a": 255}],
        expected=[{"_id": 2, "a": 35}, {"_id": 3, "a": 255}],
        msg="Bitmask 35 (bits 0,1,5) checks those bits are set",
    ),
    QueryTestCase(
        id="numeric_bitmask_partial_set_fails",
        filter={"a": {"$bitsAllSet": [1, 3]}},
        doc=[{"_id": 1, "a": 54}, {"_id": 2, "a": 10}],
        expected=[{"_id": 2, "a": 10}],
        msg="a=54 (00110110): bit 1 is SET, bit 3 is CLEAR — partial set does not match",
    ),
    QueryTestCase(
        id="numeric_bitmask_int64_max",
        filter={"a": {"$bitsAllSet": INT64_MAX}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -1}],
        msg="Int64 max as bitmask requires all 63 bits set",
    ),
    QueryTestCase(
        id="numeric_bitmask_decimal128",
        filter={"a": {"$bitsAllSet": Decimal128("35")}},
        doc=[{"_id": 1, "a": 35}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 35}],
        msg="Decimal128 within int64 range accepted as numeric bitmask",
    ),
    QueryTestCase(
        id="numeric_bitmask_decimal128_exponential",
        filter={"a": {"$bitsAllSet": Decimal128("1E+2")}},
        doc=[{"_id": 1, "a": 255}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 255}],
        msg="Decimal128 exponential notation (100) accepted as numeric bitmask",
    ),
]

VALID_BINDATA_BITMASK_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_bitmask_empty",
        filter={"a": {"$bitsAllSet": Binary(b"")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        msg="Empty BinData bitmask matches all",
    ),
    QueryTestCase(
        id="bindata_bitmask_all_ones",
        filter={"a": {"$bitsAllSet": Binary(b"\xff")}},
        doc=[{"_id": 1, "a": 255}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 255}],
        msg="All-ones BinData bitmask",
    ),
    QueryTestCase(
        id="bindata_bitmask_subtype_1",
        filter={"a": {"$bitsAllSet": Binary(b"\x01", 1)}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 1}],
        msg="BinData with subtype 1 works as bitmask",
    ),
]

VALID_POSITION_LIST_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="position_list_empty",
        filter={"a": {"$bitsAllSet": []}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        msg="Empty position list matches all",
    ),
    QueryTestCase(
        id="position_list_single_bit0",
        filter={"a": {"$bitsAllSet": [0]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 0}, {"_id": 3, "a": 3}],
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="Single position [0] checks bit 0 is set",
    ),
    QueryTestCase(
        id="position_list_mid_range_bits",
        filter={"a": {"$bitsAllSet": [30, 32, 34, 36, 38, 40]}},
        doc=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": Int64(10737418240)},
            {"_id": 3, "a": Int64(1465657589760)},
        ],
        expected=[{"_id": 3, "a": Int64(1465657589760)}],
        msg="Mid-range positions spanning byte boundaries 3-5",
    ),
    QueryTestCase(
        id="position_list_decimal128_values",
        filter={"a": {"$bitsAllSet": [Decimal128("0"), Decimal128("1")]}},
        doc=[{"_id": 1, "a": 3}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 3}],
        msg="Decimal128 integer values accepted as positions",
    ),
    QueryTestCase(
        id="position_list_all_64_bits",
        filter={"a": {"$bitsAllSet": list(range(64))}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -1}],
        msg="All 64 positions [0..63] requires all bits set",
    ),
]

ALL_TESTS = VALID_NUMERIC_BITMASK_TESTS + VALID_BINDATA_BITMASK_TESTS + VALID_POSITION_LIST_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAllSet_valid_arguments(collection, test):
    """Test $bitsAllSet with valid bitmask forms (numeric, BinData, position list)."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
