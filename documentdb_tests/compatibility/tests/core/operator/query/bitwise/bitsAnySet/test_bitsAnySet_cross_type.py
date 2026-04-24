"""
Tests for $bitsAnySet BinData and Decimal128 specific behavior.

Validates BinData subtype handling (0, 1, 2, 3, 4, 5, 6, 128),
variable-length BinData with zero extension,
little-endian byte order for BinData bitmasks, cross-type field/bitmask combinations,
and Decimal128 field values including negative two's complement, negative zero,
boundary values, and array-of-Decimal128 matching.

Decimal128 skip cases (NaN, Infinity, beyond-int64) are covered by test_bitwise_common.py.
"""

import pytest
from bson import Binary, Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
)

BINDATA_SUBTYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_subtype_0",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            {"_id": 1, "a": Binary(b"\x06", 0)},
            {"_id": 2, "a": Binary(b"\x01", 0)},
        ],
        # Driver converts BinData subtype 0 to raw bytes, so raw bytes is expected
        expected=[{"_id": 2, "a": b"\x01"}],
        msg="BinData subtype 0 (generic) bit checking works; 0x01 has bit 0 set",
    ),
    QueryTestCase(
        id="bindata_subtype_1",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            {"_id": 1, "a": Binary(b"\x06", 1)},
            {"_id": 2, "a": Binary(b"\x01", 1)},
        ],
        expected=[{"_id": 2, "a": Binary(b"\x01", 1)}],
        msg="BinData subtype 1 (function) same bit checking",
    ),
    QueryTestCase(
        id="bindata_subtype_2_length_prefix",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            # Subtype 2 (old binary) stores a 4-byte length prefix before the data.
            # For Binary(b"\x06", 2), the raw stored bytes are: 01 00 00 00 06
            #   Bit  0-7:  00000001  ← length prefix, bit 0 is SET
            #   Bit  8-15: 00000000
            #   Bit 16-23: 00000000
            #   Bit 24-31: 00000000
            #   Bit 32-39: 00000110  ← actual data (0x06), bits 33,34 set
            # Bitwise operators evaluate against these raw stored bytes,
            # so bit 0 is set (from length prefix 0x01).
            {"_id": 1, "a": Binary(b"\x06", 2)},
            {"_id": 2, "a": Binary(b"\x01", 2)},
            {"_id": 3, "a": Binary(b"\x06", 128)},  # subtype 128, bit 0 clear
        ],
        expected=[
            {"_id": 1, "a": Binary(b"\x06", 2)},
            {"_id": 2, "a": Binary(b"\x01", 2)},
        ],
        msg="BinData subtype 2 (old binary) has a 4-byte length prefix that shifts bit layout; "
        "bit 0 comes from prefix byte 0x01, so it is set and matches $bitsAnySet",
    ),
    QueryTestCase(
        id="bindata_subtype_128",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            {"_id": 1, "a": Binary(b"\x06", 128)},
            {"_id": 2, "a": Binary(b"\x01", 128)},
        ],
        expected=[{"_id": 2, "a": Binary(b"\x01", 128)}],
        msg="BinData subtype 128 (user-defined) bit checking works",
    ),
    QueryTestCase(
        id="bindata_subtypes_3_4_5_6",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            # bit 0 set (first byte odd) — should match
            {
                "_id": 1,
                "a": Binary(b"\x07\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 3),
            },
            {
                "_id": 2,
                "a": Binary(b"\x07\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 4),
            },
            {
                "_id": 3,
                "a": Binary(b"\xe9\x9a\x18\xc4\x28\xcb\x38\xd5\xf2\x60\x85\x36\x78\x92\x2e\x03", 5),
            },
            {
                "_id": 4,
                "a": Binary(b"\x07\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 6),
            },
            # bit 0 clear (first byte even) — should not match
            {
                "_id": 5,
                "a": Binary(b"\x06\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 3),
            },
            {
                "_id": 6,
                "a": Binary(b"\x06\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 4),
            },
            {
                "_id": 7,
                "a": Binary(b"\xd4\x1d\x8c\xd9\x8f\x00\xb2\x04\xe9\x80\x09\x98\xec\xf8\x42\x7e", 5),
            },
            {
                "_id": 8,
                "a": Binary(b"\x06\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 6),
            },
        ],
        expected=[
            {
                "_id": 1,
                "a": Binary(b"\x07\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 3),
            },
            {
                "_id": 2,
                "a": Binary(b"\x07\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 4),
            },
            {
                "_id": 3,
                "a": Binary(b"\xe9\x9a\x18\xc4\x28\xcb\x38\xd5\xf2\x60\x85\x36\x78\x92\x2e\x03", 5),
            },
            {
                "_id": 4,
                "a": Binary(b"\x07\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff", 6),
            },
        ],
        msg="Subtypes 3 (UUID old), 4 (UUID), 5 (MD5), 6 (C# legacy UUID): "
        "bit 0 set → matches; bit 0 clear → does not match",
    ),
]

VARIABLE_LENGTH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_1byte_zero_ext_bit8",
        filter={"a": {"$bitsAnySet": [8]}},
        doc=[{"_id": 1, "a": Binary(b"\xff", 128)}],
        expected=[],
        msg="1-byte BinData: bit 8 beyond data is zero-extended (clear) → no match",
    ),
    QueryTestCase(
        id="bindata_1byte_bit0_set",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": Binary(b"\xc3", 128)}],
        expected=[{"_id": 1, "a": Binary(b"\xc3", 128)}],
        msg="BinData 0xC3 (11000011): bit 0 is set → matches",
    ),
    QueryTestCase(
        id="bindata_1byte_bit2_clear",
        filter={"a": {"$bitsAnySet": [2]}},
        doc=[{"_id": 1, "a": Binary(b"\xc3", 128)}],
        expected=[],
        msg="BinData 0xC3 (11000011): bit 2 is clear → no match",
    ),
    QueryTestCase(
        id="bindata_1byte_bit200_zero_ext",
        filter={"a": {"$bitsAnySet": [200]}},
        doc=[{"_id": 1, "a": Binary(b"\xc3", 128)}],
        expected=[],
        msg="BinData 1 byte: bit 200 zero-extended → clear → no match",
    ),
    QueryTestCase(
        id="bindata_2byte_bit15_check",
        filter={"a": {"$bitsAnySet": [15]}},
        doc=[
            {"_id": 1, "a": Binary(b"\xff\x7f", 128)},
            {"_id": 2, "a": Binary(b"\xff\xff", 128)},
        ],
        expected=[{"_id": 2, "a": Binary(b"\xff\xff", 128)}],
        msg="2-byte BinData: bit 15 set only in 0xFFFF",
    ),
    QueryTestCase(
        id="bindata_2byte_zero_ext_bit16",
        filter={"a": {"$bitsAnySet": [16]}},
        doc=[{"_id": 1, "a": Binary(b"\xff\xff", 128)}],
        expected=[],
        msg="2-byte BinData: bit 16 beyond data is zero-extended (clear) → no match",
    ),
    QueryTestCase(
        id="bindata_20byte_bit159_check",
        filter={"a": {"$bitsAnySet": [159]}},
        doc=[
            {"_id": 1, "a": Binary(b"\xff" * 20, 128)},
            {"_id": 2, "a": Binary(b"\xff" * 19 + b"\x7f", 128)},
        ],
        expected=[{"_id": 1, "a": Binary(b"\xff" * 20, 128)}],
        msg="20-byte BinData: bit 159 set only in all-FF doc",
    ),
]

LITTLE_ENDIAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bindata_little_endian_byte_order",
        filter={"a": {"$bitsAnySet": Binary(b"\x00\x20")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 8192}],
        expected=[{"_id": 2, "a": 8192}],
        msg="BinData [0x00, 0x20] little-endian checks bit 13; 8192=2^13",
    ),
    QueryTestCase(
        id="bindata_little_endian_equiv_position_13",
        filter={"a": {"$bitsAnySet": [13]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 8192}],
        expected=[{"_id": 2, "a": 8192}],
        msg="Position [13] equivalent to BinData [0x00, 0x20]",
    ),
]

CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_field_with_bindata_bitmask",
        filter={"a": {"$bitsAnySet": Binary(b"\x01")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="Numeric field with BinData bitmask checking bit 0",
    ),
    QueryTestCase(
        id="bindata_field_with_position_list",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[
            {"_id": 1, "a": Binary(b"\x06", 128)},
            {"_id": 2, "a": Binary(b"\x01", 128)},
        ],
        expected=[{"_id": 2, "a": Binary(b"\x01", 128)}],
        msg="BinData field with position list bitmask",
    ),
    QueryTestCase(
        id="bindata_field_with_longer_bindata_bitmask",
        filter={"a": {"$bitsAnySet": Binary(b"\x01\x00\x00")}},
        doc=[
            {"_id": 1, "a": Binary(b"\x06", 128)},
            {"_id": 2, "a": Binary(b"\x01", 128)},
        ],
        expected=[{"_id": 2, "a": Binary(b"\x01", 128)}],
        msg="BinData field with BinData bitmask of different length",
    ),
    QueryTestCase(
        id="numeric_field_with_large_bindata_bitmask",
        filter={"a": {"$bitsAnySet": Binary(b"\x01\x00\x00\x00\x00")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="Numeric field with BinData bitmask longer than needed",
    ),
]

DECIMAL128_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal128_zero_none_set",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[{"_id": 1, "a": DECIMAL128_ZERO}],
        expected=[],
        msg="Decimal128 zero has no bits set",
    ),
    QueryTestCase(
        id="decimal128_negative_zero",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            {"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 2, "a": Decimal128("1")},
        ],
        expected=[{"_id": 2, "a": Decimal128("1")}],
        msg="Decimal128 negative zero treated as integer 0, no bits set",
    ),
    QueryTestCase(
        id="decimal128_neg1_all_set",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[{"_id": 1, "a": Decimal128("-1")}, {"_id": 2, "a": DECIMAL128_ZERO}],
        expected=[{"_id": 1, "a": Decimal128("-1")}],
        msg="Decimal128 -1 has all bits set",
    ),
    QueryTestCase(
        id="decimal128_neg2_bit0_clear",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            {"_id": 1, "a": Decimal128("-2")},
            {"_id": 2, "a": Decimal128("-1")},
        ],
        expected=[{"_id": 2, "a": Decimal128("-1")}],
        msg="Decimal128 -2: bit 0 clear in two's complement; -1 has bit 0 set",
    ),
    QueryTestCase(
        id="decimal128_at_int64_max",
        filter={"a": {"$bitsAnySet": [63]}},
        doc=[{"_id": 1, "a": Decimal128("9223372036854775807")}],
        expected=[],
        msg="Decimal128 at INT64_MAX: bit 63 is clear, no match",
    ),
    QueryTestCase(
        id="decimal128_array_any_element",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            {"_id": 1, "a": [Decimal128("20"), Decimal128("1")]},
            {"_id": 2, "a": [Decimal128("20"), Decimal128("0")]},
        ],
        expected=[{"_id": 1, "a": [Decimal128("20"), Decimal128("1")]}],
        msg="Array of Decimal128 matches if any element has bit 0 set",
    ),
]

ALL_TESTS = (
    BINDATA_SUBTYPE_TESTS
    + VARIABLE_LENGTH_TESTS
    + LITTLE_ENDIAN_TESTS
    + CROSS_TYPE_TESTS
    + DECIMAL128_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAnySet_cross_type(collection, test):
    """Test $bitsAnySet with BinData subtypes, variable-length, and Decimal128 field values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
