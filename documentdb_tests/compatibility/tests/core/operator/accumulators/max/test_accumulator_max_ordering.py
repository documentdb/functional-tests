"""Tests for $max accumulator BSON comparison order and within-type ordering."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

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
# 1. BSON Comparison Order (Cross-Type)
# ===========================================================================

# Property [BSON Comparison Order]: $max compares values using BSON comparison
# order when documents contain different types.
# BSON order: MinKey < Number < String < Object < Array < Binary < ObjectId
# < Boolean < Date < Timestamp < Regex < Code < MaxKey.
MAX_BSON_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_minkey_vs_number",
        docs=[{"v": MinKey()}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should pick number over MinKey per BSON order",
    ),
    AccumulatorTestCase(
        "bson_number_vs_string",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$max should pick string over number per BSON order",
    ),
    AccumulatorTestCase(
        "bson_string_vs_object",
        docs=[{"v": "zzz"}, {"v": {"a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 1}}],
        msg="$max should pick object over string per BSON order",
    ),
    AccumulatorTestCase(
        "bson_object_vs_array",
        docs=[{"v": {"z": 99}}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1]}],
        msg="$max should pick array over object per BSON order",
    ),
    AccumulatorTestCase(
        "bson_array_vs_binary",
        docs=[{"v": [999]}, {"v": Binary(b"\x00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x00"}],
        msg="$max should pick binary over array per BSON order",
    ),
    AccumulatorTestCase(
        "bson_binary_vs_objectid",
        docs=[{"v": Binary(b"\xff" * 100)}, {"v": ObjectId("000000000000000000000001")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000000000000000000001")}],
        msg="$max should pick ObjectId over binary per BSON order",
    ),
    AccumulatorTestCase(
        "bson_objectid_vs_boolean",
        docs=[{"v": ObjectId("ffffffffffffffffffffffff")}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick boolean over ObjectId per BSON order",
    ),
    AccumulatorTestCase(
        "bson_boolean_vs_datetime",
        docs=[{"v": True}, {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$max should pick datetime over boolean per BSON order",
    ),
    AccumulatorTestCase(
        "bson_datetime_vs_timestamp",
        docs=[
            {"v": datetime(9999, 12, 31, tzinfo=timezone.utc)},
            {"v": Timestamp(0, 1)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(0, 1)}],
        msg="$max should pick timestamp over datetime per BSON order",
    ),
    AccumulatorTestCase(
        "bson_timestamp_vs_regex",
        docs=[{"v": Timestamp(4294967295, 4294967295)}, {"v": Regex("a")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("a")}],
        msg="$max should pick regex over timestamp per BSON order",
    ),
    # NOTE: bson_regex_vs_code, bson_code_vs_maxkey, and bson_minkey_vs_maxkey
    # are stage-dependent and tested in test_accumulator_max_stage_divergence.py.
    AccumulatorTestCase(
        "bson_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "bson_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "bson_string_before_number",
        docs=[{"v": "a"}, {"v": 999999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "a"}],
        msg="$max should pick string over number regardless of insertion order",
    ),
    # NOTE: bson_maxkey_before_minkey is stage-dependent and tested in
    # test_accumulator_max_stage_divergence.py.
]


# ===========================================================================
# 2. Within-Type Ordering
# ===========================================================================

# Property [Numeric Comparison]: values of the same numeric type are compared
# numerically; cross-type numeric comparisons use numeric value.

# 2a. Numeric comparison
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
        "numeric_ieee754_rounding",
        docs=[{"v": 3.14}, {"v": Decimal128("3.14")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 3.14}],
        msg="$max should pick double 3.14 over Decimal128 3.14 (IEEE 754 rounding)",
    ),
]

# 2b. String comparison
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
]

# 2c. Boolean ordering
MAX_BOOLEAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boolean_true_vs_false",
        docs=[{"v": True}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over False",
    ),
    AccumulatorTestCase(
        "boolean_false_vs_true",
        docs=[{"v": False}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over False regardless of insertion order",
    ),
]

# 2d. Datetime ordering
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

# 2e. Timestamp ordering
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

# 2f. ObjectId ordering
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

# 2g. Binary ordering
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

# 2h. Regex ordering
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

# 2i. Object (embedded document) ordering
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

# 2j. Array ordering (as values, NOT traversed in accumulator context)
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
# 3. BSON Type Distinction
# ===========================================================================

# Property [BSON Type Distinction]: values of different BSON types are
# distinct even when they appear similar.
MAX_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ""}],
        msg="$max should exclude null and return empty string",
    ),
    AccumulatorTestCase(
        "distinct_numeric_string",
        docs=[{"v": "123"}, {"v": 1000000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "123"}],
        msg="$max should pick string '123' over int 1000000 (string > number, no coercion)",
    ),
]


# ===========================================================================
# Combined success tests and test function
# ===========================================================================

MAX_ORDERING_SUCCESS_TESTS = (
    MAX_BSON_ORDER_TESTS
    + MAX_NUMERIC_TESTS
    + MAX_STRING_TESTS
    + MAX_BOOLEAN_TESTS
    + MAX_DATETIME_TESTS
    + MAX_TIMESTAMP_TESTS
    + MAX_OBJECTID_TESTS
    + MAX_BINARY_TESTS
    + MAX_REGEX_TESTS
    + MAX_OBJECT_TESTS
    + MAX_ARRAY_TESTS
    + MAX_TYPE_DISTINCTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_ORDERING_SUCCESS_TESTS))
def test_accumulator_max_ordering(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator BSON comparison order and within-type ordering via $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
