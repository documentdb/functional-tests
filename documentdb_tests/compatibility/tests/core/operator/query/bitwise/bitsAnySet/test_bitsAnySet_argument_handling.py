"""
Tests for $bitsAnySet valid argument handling.

Validates valid bitmask forms (numeric, BinData, position list).
Error cases are covered in test_bitwise_common.py.
"""

import pytest
from bson import Binary, Decimal128, Int64

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
    INT32_MAX,
    INT64_MAX,
)

VALID_NUMERIC_BITMASK_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_bitmask_zero",
        filter={"a": {"$bitsAnySet": 0}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": -1}],
        expected=[],
        msg="Bitmask 0 has no bits to check, matches nothing",
    ),
    QueryTestCase(
        id="numeric_bitmask_1",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": 2}],
        expected=[{"_id": 2, "a": 1}],
        msg="Bitmask 1 checks bit 0; matches where bit 0 is set",
    ),
    QueryTestCase(
        id="numeric_bitmask_35",
        filter={"a": {"$bitsAnySet": 35}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 35}, {"_id": 3, "a": 54}],
        expected=[{"_id": 2, "a": 35}, {"_id": 3, "a": 54}],
        msg="Bitmask 35 (bits 0,1,5) matches where ANY of those bits is set; "
        "also serves as numeric form baseline for three-form equivalence",
    ),
    QueryTestCase(
        id="numeric_bitmask_255",
        filter={"a": {"$bitsAnySet": 255}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": 54}],
        expected=[{"_id": 2, "a": 255}, {"_id": 3, "a": 54}],
        msg="Bitmask 255 (bits 0-7) matches where any of bits 0-7 is set",
    ),
    QueryTestCase(
        id="numeric_bitmask_int64_max",
        filter={"a": {"$bitsAnySet": INT64_MAX}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="INT64_MAX as bitmask: any value with any of bits 0-62 set matches",
    ),
    QueryTestCase(
        id="numeric_bitmask_double_whole_3",
        filter={"a": {"$bitsAnySet": 3.0}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 3}],
        expected=[{"_id": 2, "a": 3}],
        msg="Whole-number double 3.0 accepted as equivalent to int 3",
    ),
    QueryTestCase(
        id="numeric_bitmask_double_zero",
        filter={"a": {"$bitsAnySet": 0.0}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="Double 0.0 as bitmask: no bits to check, matches nothing",
    ),
    QueryTestCase(
        id="numeric_bitmask_negative_zero",
        filter={"a": {"$bitsAnySet": DOUBLE_NEGATIVE_ZERO}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="Negative zero -0.0 treated as 0, no bits to check",
    ),
    QueryTestCase(
        id="numeric_bitmask_int64_35",
        filter={"a": {"$bitsAnySet": Int64(35)}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 35}],
        expected=[{"_id": 2, "a": 35}],
        msg="Int64(35) accepted as numeric bitmask",
    ),
    QueryTestCase(
        id="numeric_bitmask_int64_zero",
        filter={"a": {"$bitsAnySet": Int64(0)}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="Int64(0) as bitmask: no bits to check",
    ),
    QueryTestCase(
        id="numeric_bitmask_decimal128_35",
        filter={"a": {"$bitsAnySet": Decimal128("35")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 35}],
        expected=[{"_id": 2, "a": 35}],
        msg="Decimal128 within int64 range accepted as numeric bitmask",
    ),
    QueryTestCase(
        id="numeric_bitmask_decimal128_zero",
        filter={"a": {"$bitsAnySet": DECIMAL128_ZERO}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="Decimal128('0') as bitmask: no bits to check",
    ),
    QueryTestCase(
        id="numeric_bitmask_decimal128_negative_zero",
        filter={"a": {"$bitsAnySet": DECIMAL128_NEGATIVE_ZERO}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="Decimal128('-0') treated as 0, no bits to check",
    ),
]

VALID_BINDATA_BITMASK_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_bitmask_empty",
        filter={"a": {"$bitsAnySet": Binary(b"")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="Empty BinData bitmask: no bits to check, matches nothing",
    ),
    QueryTestCase(
        id="bindata_bitmask_all_zeros",
        filter={"a": {"$bitsAnySet": Binary(b"\x00")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="BinData 0x00: no bits set in mask, matches nothing",
    ),
    QueryTestCase(
        id="bindata_bitmask_all_ones",
        filter={"a": {"$bitsAnySet": Binary(b"\xff")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": 54}],
        expected=[{"_id": 2, "a": 255}, {"_id": 3, "a": 54}],
        msg="BinData 0xFF: matches where any of bits 0-7 is set",
    ),
    QueryTestCase(
        id="bindata_bitmask_subtype_1",
        filter={"a": {"$bitsAnySet": Binary(b"\x03", 1)}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 3}],
        expected=[{"_id": 2, "a": 3}],
        msg="BinData with subtype 1 works as bitmask",
    ),
]

VALID_POSITION_LIST_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="position_list_empty",
        filter={"a": {"$bitsAnySet": []}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        expected=[],
        msg="Empty position list: no positions to check, matches nothing",
    ),
    QueryTestCase(
        id="position_list_single_bit0",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": 2}],
        expected=[{"_id": 2, "a": 1}],
        msg="Single position [0] checks bit 0; only 1 has bit 0 set",
    ),
    QueryTestCase(
        id="position_list_multiple",
        filter={"a": {"$bitsAnySet": [1, 5]}},
        doc=[{"_id": 1, "a": 20}, {"_id": 2, "a": 15}, {"_id": 3, "a": 54}],
        expected=[{"_id": 2, "a": 15}, {"_id": 3, "a": 54}],
        msg="Positions [1,5] matches where bit 1 or bit 5 is set; "
        "20 (10100) has neither bit 1 nor 5 set",
    ),
    QueryTestCase(
        id="position_list_all_byte_bits",
        filter={"a": {"$bitsAnySet": [0, 1, 2, 3, 4, 5, 6, 7]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": 54}],
        expected=[{"_id": 2, "a": 255}, {"_id": 3, "a": 54}],
        msg="All 8 bit positions: matches where any of bits 0-7 is set",
    ),
    QueryTestCase(
        id="position_list_large_position",
        filter={"a": {"$bitsAnySet": [100]}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": -1}],
        expected=[{"_id": 2, "a": -1}],
        msg="Large position [100]: set for negative (sign-extended), "
        "clear for positive (zero-extended)",
    ),
    QueryTestCase(
        id="position_list_decimal128_values",
        filter={"a": {"$bitsAnySet": [Decimal128("0"), Decimal128("1")]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 3}],
        expected=[{"_id": 2, "a": 3}],
        msg="Decimal128 integer values accepted as positions",
    ),
    QueryTestCase(
        id="position_list_all_64_bits",
        filter={"a": {"$bitsAnySet": list(range(64))}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": -1}],
        expected=[{"_id": 2, "a": -1}],
        msg="All 64 positions [0..63]: -1 has all bits set; 0 has none set",
    ),
    QueryTestCase(
        id="position_list_duplicate_positions",
        filter={"a": {"$bitsAnySet": [0, 0, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="Duplicate positions behave same as deduplicated [0]",
    ),
    QueryTestCase(
        id="position_list_unsorted",
        filter={"a": {"$bitsAnySet": [5, 1, 3]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 42}, {"_id": 3, "a": 54}],
        expected=[{"_id": 2, "a": 42}, {"_id": 3, "a": 54}],
        msg="Unsorted positions [5,1,3] accepted; "
        "42 (101010) has all 3 set, 54 (110110) has bits 1,5 set",
    ),
    QueryTestCase(
        id="position_list_mid_range_bits",
        filter={"a": {"$bitsAnySet": [30, 32, 34, 36, 38, 40]}},
        doc=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": Int64(10737418240)},
            {"_id": 3, "a": Int64(1465657589760)},
        ],
        expected=[
            {"_id": 3, "a": Int64(1465657589760)},
        ],
        msg="Mid-range positions spanning byte boundaries 3-5; "
        "doc 2 (0x280000000) has bits 31,33 set — none in queried positions; "
        "doc 3 (0x15540000000) has bits 30,32,34,36,38,40 set",
    ),
    QueryTestCase(
        id="position_list_int32_max",
        filter={"a": {"$bitsAnySet": [INT32_MAX]}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": -1}],
        expected=[{"_id": 2, "a": -1}],
        msg="INT32_MAX as position accepted; -1 has all bits set via sign extension",
    ),
]

ALL_VALID_TESTS = (
    VALID_NUMERIC_BITMASK_TESTS + VALID_BINDATA_BITMASK_TESTS + VALID_POSITION_LIST_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_VALID_TESTS))
def test_bitsAnySet_valid_arguments(collection, test):
    """Test $bitsAnySet with valid bitmask forms (numeric, BinData, position list)."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
