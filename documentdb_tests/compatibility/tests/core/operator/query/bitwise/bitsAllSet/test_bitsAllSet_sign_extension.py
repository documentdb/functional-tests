"""
Tests for $bitsAllSet sign extension, edge cases, and boundary values.

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
        filter={"a": {"$bitsAllSet": [0]}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -1}],
        msg="-1 has all bits set, bit 0 is set",
    ),
    QueryTestCase(
        id="negative_sign_extended_high_bit",
        filter={"a": {"$bitsAllSet": [200]}},
        doc=[{"_id": 1, "a": -5}, {"_id": 2, "a": 5}],
        expected=[{"_id": 1, "a": -5}],
        msg="Negative: bit 200 SET via sign extension; positive: bit 200 NOT set",
    ),
    QueryTestCase(
        id="positive_high_bit_not_set",
        filter={"a": {"$bitsAllSet": [200]}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="Positive number: bits beyond 63 are 0, not set",
    ),
    QueryTestCase(
        id="negative_high_bit_set",
        filter={"a": {"$bitsAllSet": [200]}},
        doc=[{"_id": 1, "a": -5}],
        expected=[{"_id": 1, "a": -5}],
        msg="Negative number: bits beyond 63 are 1 due to sign extension",
    ),
    QueryTestCase(
        id="neg1_with_bitmask_zero",
        filter={"a": {"$bitsAllSet": 0}},
        doc=[{"_id": 1, "a": -1}],
        expected=[{"_id": 1, "a": -1}],
        msg="Bitmask 0 means no bits to check, matches even -1",
    ),
    QueryTestCase(
        id="neg2_bit1_set",
        filter={"a": {"$bitsAllSet": 2}},
        doc=[{"_id": 1, "a": -2}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": -2}],
        msg="-2 (binary ...11111110) has bit 1 set",
    ),
    QueryTestCase(
        id="int64_min_bit0_not_set",
        filter={"a": {"$bitsAllSet": [0]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="INT64_MIN: only bit 63 set, bit 0 is NOT set",
    ),
    QueryTestCase(
        id="int64_min_bit63_set",
        filter={"a": {"$bitsAllSet": [63]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="INT64_MIN: bit 63 is set (sign bit)",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bitmask_zero_skips_non_numeric",
        filter={"a": {"$bitsAllSet": 0}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": -1}, {"_id": 4, "a": "str"}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": -1}],
        msg="Bitmask 0 matches all integer-representable, not string",
    ),
    QueryTestCase(
        id="empty_position_list_skips_non_numeric",
        filter={"a": {"$bitsAllSet": []}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": "str"}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        msg="Empty position list matches all integer-representable, not string",
    ),
    QueryTestCase(
        id="empty_bindata_skips_non_numeric",
        filter={"a": {"$bitsAllSet": Binary(b"")}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}, {"_id": 3, "a": "str"}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 255}],
        msg="Empty BinData matches all integer-representable, not string",
    ),
    QueryTestCase(
        id="large_double_1e18_representable",
        filter={"a": {"$bitsAllSet": 1}},
        doc=[{"_id": 1, "a": 1e18}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 2, "a": 1.0}],
        msg="1e18 is representable as int64 but bit 0 is not set; 1.0 has bit 0 set",
    ),
    QueryTestCase(
        id="duplicate_positions_ignored",
        filter={"a": {"$bitsAllSet": [0, 0, 0]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 1}],
        msg="Duplicate positions behave same as deduplicated [0]",
    ),
]

BOUNDARY_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_max_lower_bits_set",
        filter={"a": {"$bitsAllSet": [0, 1, 2, 3, 4, 5, 6, 7]}},
        doc=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT32_MAX}],
        msg="INT32_MAX (0x7FFFFFFF) has all lower bits set",
    ),
    QueryTestCase(
        id="int32_min_bit31_set",
        filter={"a": {"$bitsAllSet": [31]}},
        doc=[{"_id": 1, "a": INT32_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="INT32_MIN: bit 31 is set (sign bit in 32-bit representation)",
    ),
    QueryTestCase(
        id="int64_max_with_bitmask_zero",
        filter={"a": {"$bitsAllSet": 0}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="INT64_MAX with bitmask 0 matches",
    ),
    QueryTestCase(
        id="neg1_matches_any_bitmask",
        filter={"a": {"$bitsAllSet": 255}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -1}],
        msg="Field value -1 has all bits set, matches any bitmask",
    ),
    QueryTestCase(
        id="position_0_is_lowest_bit",
        filter={"a": {"$bitsAllSet": [0]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 1}],
        msg="Position 0 is the lowest bit",
    ),
    QueryTestCase(
        id="position_63_is_highest_bit",
        filter={"a": {"$bitsAllSet": [63]}},
        doc=[{"_id": 1, "a": Int64(-1)}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": Int64(-1)}],
        msg="Position 63 is the highest bit in 64-bit signed integer",
    ),
    QueryTestCase(
        id="decimal128_int64_max_as_bitmask",
        filter={"a": {"$bitsAllSet": Decimal128("9223372036854775807")}},
        doc=[{"_id": 1, "a": -1}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": -1}],
        msg="Decimal128 at int64 max boundary accepted as bitmask",
    ),
]

ALL_TESTS = SIGN_EXTENSION_TESTS + EDGE_CASE_TESTS + BOUNDARY_VALUE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAllSet_sign_extension_and_edge_cases(collection, test):
    """Test $bitsAllSet sign extension, two's complement, edge cases, and boundary values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
