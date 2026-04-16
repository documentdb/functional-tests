"""
Tests for $bitsAllSet cross-type behavior.

Validates BinData subtype handling, variable-length BinData with zero extension,
little-endian byte order for BinData bitmasks, and Decimal128 field values including
integer-representable, negative two's complement, negative zero, and array-of-Decimal128
matching.
"""

import pytest
from bson import Binary, Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BINDATA_SUBTYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_subtype_0",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Binary(b"\x03")}, {"_id": 2, "a": Binary(b"\x06")}],
        # driver automatically converts subtype 0 to raw bytes,
        # so expected is in raw form instead of Binary(b"\x03", 0)
        expected=[{"_id": 1, "a": b"\x03"}],
        msg="BinData subtype 128 (user-defined) bit checking works",
    ),
    QueryTestCase(
        id="bindata_subtype_1",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Binary(b"\x03", 1)}, {"_id": 2, "a": Binary(b"\x06", 1)}],
        expected=[{"_id": 1, "a": Binary(b"\x03", 1)}],
        msg="BinData subtype 1 (function) same bit checking",
    ),
    QueryTestCase(
        id="bindata_subtype_2_length_prefixed",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Binary(b"\x03", 2)}, {"_id": 2, "a": Binary(b"\x06", 2)}],
        expected=[{"_id": 1, "a": Binary(b"\x03", 2)}, {"_id": 2, "a": Binary(b"\x06", 2)}],
        msg="BinData subtype 2 (old binary) has length prefix, checks prefixed data",
    ),
    QueryTestCase(
        id="bindata_subtype_128",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Binary(b"\x03", 128)}, {"_id": 2, "a": Binary(b"\x06", 128)}],
        expected=[{"_id": 1, "a": Binary(b"\x03", 128)}],
        msg="BinData subtype 128 (user-defined) bit checking works",
    ),
]

VARIABLE_LENGTH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_1byte_zero_ext_bit8",
        filter={"a": {"$bitsAllSet": [8]}},
        doc=[{"_id": 1, "a": Binary(b"\xff", 128)}],
        expected=[],
        msg="1-byte BinData: bit 8 beyond data is zero-extended (not set)",
    ),
    QueryTestCase(
        id="bindata_2byte_bit15_check",
        filter={"a": {"$bitsAllSet": [15]}},
        doc=[
            {"_id": 1, "a": Binary(b"\xff\xff", 128)},
            {"_id": 2, "a": Binary(b"\xff\x7f", 128)},
        ],
        expected=[{"_id": 1, "a": Binary(b"\xff\xff", 128)}],
        msg="2-byte BinData: bit 15 check",
    ),
    QueryTestCase(
        id="bindata_2byte_zero_ext_bit16",
        filter={"a": {"$bitsAllSet": [16]}},
        doc=[{"_id": 1, "a": Binary(b"\xff\xff", 128)}],
        expected=[],
        msg="2-byte BinData: bit 16 beyond data is zero-extended (not set)",
    ),
    QueryTestCase(
        id="bindata_20byte_bit159_check",
        filter={"a": {"$bitsAllSet": [159]}},
        doc=[
            {"_id": 1, "a": Binary(b"\xff" * 20, 128)},
            {"_id": 2, "a": Binary(b"\xff" * 19 + b"\x7f", 128)},
        ],
        expected=[{"_id": 1, "a": Binary(b"\xff" * 20, 128)}],
        msg="20-byte BinData: bit 159 check",
    ),
]

LITTLE_ENDIAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_little_endian_byte_order",
        filter={"a": {"$bitsAllSet": Binary(b"\x00\x20")}},
        doc=[{"_id": 1, "a": 8192}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 8192}],
        msg="BinData [0x00, 0x20] little-endian checks bit 13",
    ),
    QueryTestCase(
        id="bindata_little_endian_equiv_position_13",
        filter={"a": {"$bitsAllSet": [13]}},
        doc=[{"_id": 1, "a": 8192}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 8192}],
        msg="Position [13] equivalent to BinData [0x00, 0x20]",
    ),
]

DECIMAL128_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_bitmask_on_decimal128_field",
        filter={"a": {"$bitsAllSet": Binary(b"\x01")}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("2")}],
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="BinData bitmask checks bit 0 on Decimal128 field values",
    ),
    QueryTestCase(
        id="decimal128_integer_bit0_set",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": Decimal128("20")}],
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="Decimal128 integer value works like int",
    ),
    QueryTestCase(
        id="decimal128_zero_no_bits_set",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Decimal128("0")}],
        expected=[],
        msg="Decimal128 zero has no bits set",
    ),
    QueryTestCase(
        id="decimal128_negative_zero",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Decimal128("-0")}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 2, "a": Decimal128("1")}],
        msg="Decimal128 negative zero treated as integer 0, no bits set",
    ),
    QueryTestCase(
        id="decimal128_neg1_all_set",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Decimal128("-1")}, {"_id": 2, "a": Decimal128("0")}],
        expected=[{"_id": 1, "a": Decimal128("-1")}],
        msg="Decimal128 -1 has all bits set",
    ),
    QueryTestCase(
        id="decimal128_at_int64_max",
        filter={"a": {"$bitsAllSet": 0}},
        doc=[{"_id": 1, "a": Decimal128("9223372036854775807")}],
        expected=[{"_id": 1, "a": Decimal128("9223372036854775807")}],
        msg="Decimal128 at INT64_MAX is representable",
    ),
    QueryTestCase(
        id="decimal128_neg2_twos_complement",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": Decimal128("-2")}, {"_id": 2, "a": Decimal128("-1")}],
        expected=[{"_id": 2, "a": Decimal128("-1")}],
        msg="Decimal128 -2: bit 0 clear in two's complement, -1 has bit 0 set",
    ),
    QueryTestCase(
        id="decimal128_array_any_element",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[
            {"_id": 1, "a": [Decimal128("1"), Decimal128("20")]},
            {"_id": 2, "a": [Decimal128("20"), Decimal128("4")]},
        ],
        expected=[{"_id": 1, "a": [Decimal128("1"), Decimal128("20")]}],
        msg="Array of Decimal128 matches if any element satisfies",
    ),
]

ALL_TESTS = (
    BINDATA_SUBTYPE_TESTS + VARIABLE_LENGTH_TESTS + LITTLE_ENDIAN_TESTS + DECIMAL128_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAllSet_cross_type(collection, test):
    """Test $bitsAllSet cross-type behavior with BinData and Decimal128."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
