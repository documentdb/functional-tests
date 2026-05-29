"""Tests for $max accumulator within-type ordering."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_Y2K,
    DATE_YEAR_1,
    DATE_YEAR_9999,
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# ===========================================================================
# 1. Within-Type Ordering
# ===========================================================================

# Property [Numeric Comparison]: values of the same numeric type are compared
# numerically; cross-type numeric comparisons use numeric value.

# 1a. Numeric comparison
MAX_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "numeric_int32_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30}],
        msg="$max should return the largest int32 value",
    ),
    AccumulatorTestCase(
        "numeric_int64_basic",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(300)}],
        msg="$max should return the largest int64 value",
    ),
    AccumulatorTestCase(
        "numeric_double_basic",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 3.5}],
        msg="$max should return the largest double value",
    ),
    AccumulatorTestCase(
        "numeric_decimal128_basic",
        docs=[{"v": Decimal128("1.5")}, {"v": Decimal128("3.5")}, {"v": Decimal128("2.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("3.5")}],
        msg="$max should return the largest Decimal128 value",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_int64",
        docs=[{"v": 5}, {"v": Int64(10)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(10)}],
        msg="$max should pick Int64(10) over int32(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_double",
        docs=[{"v": 5}, {"v": 10.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10.5}],
        msg="$max should pick double(10.5) over int32(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_decimal",
        docs=[{"v": 5}, {"v": Decimal128("10")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("10")}],
        msg="$max should pick Decimal128(10) over int32(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_double",
        docs=[{"v": Int64(5)}, {"v": 10.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10.5}],
        msg="$max should pick double(10.5) over Int64(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_decimal",
        docs=[{"v": Int64(5)}, {"v": Decimal128("10")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("10")}],
        msg="$max should pick Decimal128(10) over Int64(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_double_decimal",
        docs=[{"v": 5.5}, {"v": Decimal128("10")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("10")}],
        msg="$max should pick Decimal128(10) over double(5.5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_all_four_types",
        docs=[{"v": 1}, {"v": Int64(2)}, {"v": 3.0}, {"v": Decimal128("4")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("4")}],
        msg="$max should return the numerically largest across all four numeric types",
    ),
    AccumulatorTestCase(
        "numeric_double_gt_decimal_ieee754",
        docs=[{"v": 3.14}, {"v": Decimal128("3.14")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 3.14}],
        msg="$max should pick double 3.14 over Decimal128 3.14 (IEEE 754 representation)",
    ),
]

# 1b. String comparison
MAX_STRING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "abd"}],
        msg="$max should pick the lexicographically larger string",
    ),
    AccumulatorTestCase(
        "string_case",
        docs=[{"v": "a"}, {"v": "A"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "a"}],
        msg="$max should pick lowercase 'a' over uppercase 'A' (byte order)",
    ),
    AccumulatorTestCase(
        "string_digits_lexicographic",
        docs=[{"v": "9"}, {"v": "10"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "9"}],
        msg="$max should compare strings lexicographically, not numerically",
    ),
    AccumulatorTestCase(
        "string_prefix",
        docs=[{"v": "abc"}, {"v": "abcd"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "abcd"}],
        msg="$max should pick the longer string when prefix matches",
    ),
    AccumulatorTestCase(
        "string_empty_vs_nonempty",
        docs=[{"v": ""}, {"v": "a"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "a"}],
        msg="$max should pick non-empty string over empty string",
    ),
    AccumulatorTestCase(
        "string_null_byte",
        docs=[{"v": "a\x00b"}, {"v": "a\x00c"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "a\x00c"}],
        msg="$max should compare strings containing null bytes correctly",
    ),
    AccumulatorTestCase(
        "string_unicode_precomposed_over_decomposed",
        docs=[{"v": "\u00e9"}, {"v": "e\u0301"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "\u00e9"}],
        msg="$max should pick precomposed \\u00e9 (0xC3A9) over decomposed e\\u0301 (0x65CC81)",
    ),
    AccumulatorTestCase(
        "string_4byte_utf8",
        docs=[{"v": "\U0001f600"}, {"v": "\U0001f601"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "\U0001f601"}],
        msg="$max should compare 4-byte UTF-8 characters (emoji) by byte value",
    ),
]

# 1c. Boolean ordering
MAX_BOOLEAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boolean_true_over_false",
        docs=[{"v": True}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over False",
    ),
]

# 1d. Datetime ordering
MAX_DATETIME_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "datetime_chronological",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2023, 6, 15, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2023, 6, 15, tzinfo=timezone.utc)}],
        msg="$max should pick the later datetime",
    ),
    AccumulatorTestCase(
        "datetime_pre_epoch_vs_epoch",
        docs=[{"v": DATE_BEFORE_EPOCH}, {"v": DATE_EPOCH}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DATE_EPOCH}],
        msg="$max should pick epoch over pre-epoch datetime",
    ),
    AccumulatorTestCase(
        "datetime_epoch_vs_future",
        docs=[{"v": DATE_EPOCH}, {"v": DATE_Y2K}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DATE_Y2K}],
        msg="$max should pick Y2K over epoch datetime",
    ),
    AccumulatorTestCase(
        "datetime_millisecond_precision",
        docs=[
            {"v": datetime(2020, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc)}],
        msg="$max should distinguish datetimes by millisecond precision",
    ),
    AccumulatorTestCase(
        "datetime_boundaries",
        docs=[{"v": DATE_YEAR_1}, {"v": DATE_YEAR_9999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DATE_YEAR_9999}],
        msg="$max should pick year 9999 over year 1",
    ),
]

# 1e. Timestamp ordering
MAX_TIMESTAMP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "timestamp_higher_time",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(200, 1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(200, 1)}],
        msg="$max should pick the timestamp with higher time component",
    ),
    AccumulatorTestCase(
        "timestamp_same_time_higher_increment",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(100, 2)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(100, 2)}],
        msg="$max should pick the timestamp with higher increment on same time",
    ),
    AccumulatorTestCase(
        "timestamp_max_signed32",
        docs=[{"v": TS_EPOCH}, {"v": TS_MAX_SIGNED32}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": TS_MAX_SIGNED32}],
        msg="$max should handle max signed 32-bit timestamp",
    ),
    AccumulatorTestCase(
        "timestamp_max_unsigned32",
        docs=[{"v": TS_MAX_SIGNED32}, {"v": TS_MAX_UNSIGNED32}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": TS_MAX_UNSIGNED32}],
        msg="$max should handle max unsigned 32-bit timestamp",
    ),
]

# 1f. ObjectId ordering
MAX_OBJECTID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "objectid_later_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000000")},
            {"v": ObjectId("000000020000000000000000")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000020000000000000000")}],
        msg="$max should pick the ObjectId with a later timestamp",
    ),
    AccumulatorTestCase(
        "objectid_same_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000001")},
            {"v": ObjectId("000000010000000000000002")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000010000000000000002")}],
        msg="$max should pick the ObjectId with higher random bytes on same timestamp",
    ),
]

# 1g. Binary ordering
MAX_BINARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "binary_content",
        docs=[{"v": Binary(b"\x01")}, {"v": Binary(b"\x02")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x02"}],
        msg="$max should pick the binary with higher byte content",
    ),
    AccumulatorTestCase(
        "binary_subtype",
        docs=[{"v": Binary(b"\x01", 0)}, {"v": Binary(b"\x01", 5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Binary(b"\x01", 5)}],
        msg="$max should pick the binary with higher subtype on same content",
    ),
]

# 1h. Regex ordering
MAX_REGEX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "regex_pattern",
        docs=[{"v": Regex("abc", "")}, {"v": Regex("def", "")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("def", "")}],
        msg="$max should pick the regex with the higher pattern string",
    ),
    AccumulatorTestCase(
        "regex_flags",
        docs=[{"v": Regex("abc", "i")}, {"v": Regex("abc", "m")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("abc", "m")}],
        msg="$max should pick the regex with higher flag string on same pattern",
    ),
]

# 1i. Object (embedded document) ordering
MAX_OBJECT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "object_first_differing_field",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 3}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 1, "b": 3}}],
        msg="$max should pick object with greater value at first differing field",
    ),
    AccumulatorTestCase(
        "object_more_fields",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1, "b": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 1, "b": 2}}],
        msg="$max should pick object with more fields when prefix matches",
    ),
    AccumulatorTestCase(
        "object_empty_vs_nonempty",
        docs=[{"v": {}}, {"v": {"a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 1}}],
        msg="$max should pick non-empty object over empty object",
    ),
    AccumulatorTestCase(
        "object_nested",
        docs=[{"v": {"a": {"b": 1}}}, {"v": {"a": {"b": 2}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": {"b": 2}}}],
        msg="$max should compare nested objects recursively",
    ),
]

# 1j. Array ordering (as values, NOT traversed in accumulator context)
MAX_ARRAY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "array_element_by_element",
        docs=[{"v": [1, 2, 3]}, {"v": [1, 2, 4]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2, 4]}],
        msg="$max should compare arrays element by element",
    ),
    AccumulatorTestCase(
        "array_longer_prefix",
        docs=[{"v": [1, 2]}, {"v": [1, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$max should pick longer array when prefix matches",
    ),
    AccumulatorTestCase(
        "array_empty_vs_nonempty",
        docs=[{"v": []}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1]}],
        msg="$max should pick non-empty array over empty array",
    ),
    AccumulatorTestCase(
        "array_nested",
        docs=[{"v": [[1]]}, {"v": [[2]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[2]]}],
        msg="$max should compare nested arrays recursively",
    ),
]


# ===========================================================================
# Combined success tests and test function
# ===========================================================================

MAX_ORDERING_SUCCESS_TESTS = (
    MAX_NUMERIC_TESTS
    + MAX_STRING_TESTS
    + MAX_BOOLEAN_TESTS
    + MAX_DATETIME_TESTS
    + MAX_TIMESTAMP_TESTS
    + MAX_OBJECTID_TESTS
    + MAX_BINARY_TESTS
    + MAX_REGEX_TESTS
    + MAX_OBJECT_TESTS
    + MAX_ARRAY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_ORDERING_SUCCESS_TESTS))
def test_accumulator_max_ordering(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator within-type ordering via $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
