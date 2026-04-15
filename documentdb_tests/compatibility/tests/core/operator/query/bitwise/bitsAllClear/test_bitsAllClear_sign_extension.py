"""
Tests for $bitsAllClear sign extension, edge cases, and boundary values.

Validates two's complement sign extension for negative integers, BinData zero extension,
identity bitmasks (0, empty list, empty BinData), duplicate positions, large representable
doubles, and Int32/Int64/Decimal128 boundary values.
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
        id="neg1_all_bits_set",
        filter={"a": {"$bitsAllClear": [0]}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="-1 has all bits set, bit 0 is not clear",
    ),
    QueryTestCase(
        id="negative_sign_extended_high_bit",
        filter={"a": {"$bitsAllClear": [200]}},
        doc=[{"_id": 1, "a": -5}, {"_id": 2, "a": 5}],
        expected=[{"_id": 2, "a": 5}],
        msg="Negative: bit 200 SET via sign extension; positive: bit 200 CLEAR",
    ),
    QueryTestCase(
        id="positive_high_bit_clear",
        filter={"a": {"$bitsAllClear": [200]}},
        doc=[{"_id": 1, "a": 5}],
        expected=[{"_id": 1, "a": 5}],
        msg="Positive number: bits beyond 63 are 0",
    ),
    QueryTestCase(
        id="negative_high_bit_not_clear",
        filter={"a": {"$bitsAllClear": [200]}},
        doc=[{"_id": 1, "a": -5}],
        expected=[],
        msg="Negative number: bits beyond 63 are 1 due to sign extension",
    ),
    QueryTestCase(
        id="neg1_with_bitmask_zero",
        filter={"a": {"$bitsAllClear": 0}},
        doc=[{"_id": 1, "a": -1}],
        expected=[{"_id": 1, "a": -1}],
        msg="Bitmask 0 means no bits to check, matches even -1",
    ),
    QueryTestCase(
        id="neg2_bit0_clear",
        filter={"a": {"$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": -2}, {"_id": 2, "a": -1}],
        expected=[{"_id": 1, "a": -2}],
        msg="-2 (binary ...11111110) has bit 0 clear",
    ),
    QueryTestCase(
        id="int64_min_bit0_clear",
        filter={"a": {"$bitsAllClear": [0]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": -1}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="INT64_MIN: only bit 63 set, bits 0-62 clear",
    ),
    QueryTestCase(
        id="int64_min_bit63_set",
        filter={"a": {"$bitsAllClear": [63]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="INT64_MIN: bit 63 is set, not clear",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bitmask_zero_skips_non_numeric",
        filter={"a": {"$bitsAllClear": 0}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": -1}, {"_id": 4, "a": "str"}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": -1}],
        msg="Bitmask 0 matches all integer-representable, not string",
    ),
    QueryTestCase(
        id="empty_position_list_skips_non_numeric",
        filter={"a": {"$bitsAllClear": []}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": "str"}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        msg="Empty position list matches all integer-representable, not string",
    ),
    QueryTestCase(
        id="empty_bindata_skips_non_numeric",
        filter={"a": {"$bitsAllClear": Binary(b"")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": "str"}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        msg="Empty BinData matches all integer-representable, not string",
    ),
    QueryTestCase(
        id="large_double_1e18_representable",
        filter={"a": {"$bitsAllClear": 1}},
        doc=[{"_id": 1, "a": 1e18}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 1, "a": 1e18}],
        msg="1e18 is representable as int64, bit 0 is clear",
    ),
    QueryTestCase(
        id="duplicate_positions_ignored",
        filter={"a": {"$bitsAllClear": [0, 0, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": 0}],
        msg="Duplicate positions behave same as deduplicated [0]",
    ),
]

BOUNDARY_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_max_bit31_clear",
        filter={"a": {"$bitsAllClear": [31]}},
        doc=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": 0}],
        msg="INT32_MAX (0x7FFFFFFF) has bit 31 clear",
    ),
    QueryTestCase(
        id="int32_min_bit0_clear",
        filter={"a": {"$bitsAllClear": [0]}},
        doc=[{"_id": 1, "a": INT32_MIN}, {"_id": 2, "a": -1}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="INT32_MIN: bit 0 is clear",
    ),
    QueryTestCase(
        id="int64_max_with_bitmask_zero",
        filter={"a": {"$bitsAllClear": 0}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="INT64_MAX with bitmask 0 matches",
    ),
    QueryTestCase(
        id="zero_matches_any_bitmask",
        filter={"a": {"$bitsAllClear": 255}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": 0}],
        msg="Field value 0 has all bits clear",
    ),
    QueryTestCase(
        id="position_0_is_lowest_bit",
        filter={"a": {"$bitsAllClear": [0]}},
        doc=[{"_id": 1, "a": 2}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": 2}],
        msg="Position 0 is the lowest bit",
    ),
    QueryTestCase(
        id="position_63_is_highest_bit",
        filter={"a": {"$bitsAllClear": [63]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": Int64(-1)}],
        expected=[{"_id": 1, "a": 0}],
        msg="Position 63 is the highest bit in 64-bit signed integer",
    ),
    QueryTestCase(
        id="decimal128_int64_max_as_bitmask",
        filter={"a": {"$bitsAllClear": Decimal128("9223372036854775807")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": 0}],
        msg="Decimal128 at int64 max boundary accepted as bitmask",
    ),
]

ALL_TESTS = SIGN_EXTENSION_TESTS + EDGE_CASE_TESTS + BOUNDARY_VALUE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAllClear_sign_extension_and_edge_cases(collection, test):
    """Test $bitsAllClear sign extension, two's complement, edge cases, and boundary values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
