"""
Tests for $bitsAnySet sign extension, edge cases, and boundary values.

Validates two's complement sign extension for negative integers,
identity bitmasks (0, empty list, empty BinData) with non-numeric type skipping,
large representable doubles, and Int32/Int64/Decimal128 boundary values.
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
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

SIGN_EXTENSION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="neg1_bit0_set",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -1}],
        msg="-1 has all bits set, bit 0 is set",
    ),
    QueryTestCase(
        id="neg1_bit63_set",
        filter={"a": {"$bitsAnySet": [63]}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -1}],
        msg="-1 has all bits set including bit 63",
    ),
    QueryTestCase(
        id="neg1_bit200_set_sign_extension",
        filter={"a": {"$bitsAnySet": [200]}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 5}],
        expected=[{"_id": 1, "a": -1}],
        msg="-1: bit 200 set via sign extension; 5: bit 200 clear (zero-extended)",
    ),
    QueryTestCase(
        id="neg2_bit0_clear",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": -2}, {"_id": 2, "a": -1}],
        expected=[{"_id": 2, "a": -1}],
        msg="-2 (binary ...11111110) has bit 0 clear; -1 has bit 0 set",
    ),
    QueryTestCase(
        id="neg2_bit1_set",
        filter={"a": {"$bitsAnySet": [1]}},
        doc=[{"_id": 1, "a": -2}],
        expected=[{"_id": 1, "a": -2}],
        msg="-2 has bit 1 set",
    ),
    QueryTestCase(
        id="neg128_bit0_clear",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": -128}],
        expected=[],
        msg="-128 (10000000): bit 0 is clear, no match",
    ),
    QueryTestCase(
        id="neg128_bit6_clear",
        filter={"a": {"$bitsAnySet": [6]}},
        doc=[{"_id": 1, "a": -128}],
        expected=[],
        msg="-128: bit 6 is clear, no match",
    ),
    QueryTestCase(
        id="neg128_bit7_set",
        filter={"a": {"$bitsAnySet": [7]}},
        doc=[{"_id": 1, "a": -128}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -128}],
        msg="-128: bit 7 is set",
    ),
    QueryTestCase(
        id="positive_high_bit_clear",
        filter={"a": {"$bitsAnySet": [200]}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="Positive number: bits beyond 63 are 0 (clear), no match",
    ),
    QueryTestCase(
        id="negative_high_bit_set",
        filter={"a": {"$bitsAnySet": [200]}},
        doc=[{"_id": 1, "a": -5}],
        expected=[{"_id": 1, "a": -5}],
        msg="Negative number: bits beyond 63 are 1 due to sign extension",
    ),
    QueryTestCase(
        id="int64_min_bit0_clear",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": -1}],
        expected=[{"_id": 2, "a": -1}],
        msg="INT64_MIN: only bit 63 set, bit 0 clear; -1 has bit 0 set",
    ),
    QueryTestCase(
        id="int64_min_bit62_clear",
        filter={"a": {"$bitsAnySet": [62]}},
        doc=[{"_id": 1, "a": INT64_MIN}],
        expected=[],
        msg="INT64_MIN: bit 62 is clear, no match",
    ),
    QueryTestCase(
        id="int64_min_bit63_set",
        filter={"a": {"$bitsAnySet": [63]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="INT64_MIN: bit 63 is set",
    ),
    QueryTestCase(
        id="int32_min_bit0_clear",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": INT32_MIN}],
        expected=[],
        msg="INT32_MIN: bit 0 is clear, no match",
    ),
    QueryTestCase(
        id="int32_min_bit31_set",
        filter={"a": {"$bitsAnySet": [31]}},
        doc=[{"_id": 1, "a": INT32_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="INT32_MIN: bit 31 is set (sign bit for 32-bit)",
    ),
    QueryTestCase(
        id="int32_min_bit32_sign_extension",
        filter={"a": {"$bitsAnySet": [32]}},
        doc=[{"_id": 1, "a": INT32_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="INT32_MIN: bit 32 set via sign extension to 64-bit",
    ),
]

BOUNDARY_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_max_bit31_clear",
        filter={"a": {"$bitsAnySet": [31]}},
        doc=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": -1}],
        expected=[{"_id": 2, "a": -1}],
        msg="INT32_MAX (0x7FFFFFFF) has bit 31 clear; -1 has it set",
    ),
    QueryTestCase(
        id="int32_max_bit30_set",
        filter={"a": {"$bitsAnySet": [30]}},
        doc=[{"_id": 1, "a": INT32_MAX}],
        expected=[{"_id": 1, "a": INT32_MAX}],
        msg="INT32_MAX has bit 30 set",
    ),
    QueryTestCase(
        id="int64_max_bit63_clear",
        filter={"a": {"$bitsAnySet": [63]}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[],
        msg="INT64_MAX: bit 63 is clear, no match",
    ),
    QueryTestCase(
        id="int64_max_with_int64_max_bitmask",
        filter={"a": {"$bitsAnySet": INT64_MAX}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="INT64_MAX with bitmask INT64_MAX: all queried bits set, matches",
    ),
    QueryTestCase(
        id="position_0_is_lowest_bit",
        filter={"a": {"$bitsAnySet": [0]}},
        doc=[{"_id": 1, "a": 2}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="Position 0 is the lowest bit; only 1 has it set",
    ),
    QueryTestCase(
        id="position_63_is_highest_bit",
        filter={"a": {"$bitsAnySet": [63]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": Int64(-1)}],
        expected=[{"_id": 2, "a": Int64(-1)}],
        msg="Position 63 is the highest bit in 64-bit signed integer",
    ),
    QueryTestCase(
        id="large_double_1e18_representable",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[{"_id": 1, "a": 1e18}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 2, "a": 1.0}],
        msg="1e18 is representable as int64 but bit 0 is clear; 1.0 has bit 0 set",
    ),
    QueryTestCase(
        id="decimal128_int64_max_as_bitmask",
        filter={"a": {"$bitsAnySet": Decimal128("9223372036854775807")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="Decimal128 at int64 max boundary accepted as bitmask",
    ),
    QueryTestCase(
        id="powers_of_2_bit1",
        filter={"a": {"$bitsAnySet": [1]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 4}],
        expected=[{"_id": 2, "a": 2}],
        msg="Powers of 2: only 2 has bit 1 set",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bitmask_zero_skips_non_numeric",
        filter={"a": {"$bitsAnySet": 0}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": "str"}],
        expected=[],
        msg="Bitmask 0 has no bits to check so matches nothing; " "non-numeric also skipped",
    ),
    QueryTestCase(
        id="empty_position_list_skips_non_numeric",
        filter={"a": {"$bitsAnySet": []}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": "str"}],
        expected=[],
        msg="Empty position list has no bits to check so matches nothing; "
        "non-numeric also skipped",
    ),
    QueryTestCase(
        id="empty_bindata_skips_non_numeric",
        filter={"a": {"$bitsAnySet": Binary(b"")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": "str"}],
        expected=[],
        msg="Empty BinData has no bits to check so matches nothing; " "non-numeric also skipped",
    ),
]

ALL_TESTS = SIGN_EXTENSION_TESTS + BOUNDARY_VALUE_TESTS + EDGE_CASE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAnySet_sign_extension_and_edge_cases(collection, test):
    """Test $bitsAnySet sign extension, two's complement, edge cases, and boundary values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
