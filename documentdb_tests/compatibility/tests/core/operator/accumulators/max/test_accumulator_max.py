"""Tests for $max accumulator in $group, $bucket, and $bucketAuto contexts."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
    MODULO_ZERO_REMAINDER_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_Y2K,
    DATE_YEAR_1,
    DATE_YEAR_9999,
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# ===========================================================================
# Pipeline Helpers
# ===========================================================================


def _group_max(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline that computes $max."""
    return [
        {"$group": {"_id": None, "result": {"$max": accumulator}}},
        {"$project": {"_id": 0, "result": 1}},
    ]


def _bucket_max(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $bucket pipeline that computes $max."""
    return [
        {
            "$bucket": {
                "groupBy": {"$literal": 0},
                "boundaries": [-1, 1],
                "output": {"result": {"$max": accumulator}},
            }
        },
        {"$project": {"_id": 0, "result": 1}},
    ]


def _bucket_auto_max(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $bucketAuto pipeline that computes $max."""
    return [
        {
            "$bucketAuto": {
                "groupBy": {"$literal": 0},
                "buckets": 1,
                "output": {"result": {"$max": accumulator}},
            }
        },
        {"$project": {"_id": 0, "result": 1}},
    ]


def _group_max_with_type(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline that computes $max with $type projection."""
    return [
        {"$group": {"_id": None, "result": {"$max": accumulator}}},
        {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
    ]


def _run(collection, test_case: AccumulatorTestCase):
    """Insert docs and run the test case pipeline."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )


# ===========================================================================
# 1. Null and Missing Handling ($group primary)
# ===========================================================================

# Property [Null and Missing Ignored]: null values, missing fields, and
# $$REMOVE are excluded from the max computation. When no non-null/non-missing
# values remain, the result is null.
MAX_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all_null",
        docs=[{"v": None}, {"v": None}],
        pipeline=_group_max("$v"),
        expected=[{"result": None}],
        msg="$max should return null when all values are null",
    ),
    AccumulatorTestCase(
        "null_all_missing",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=_group_max("$v"),
        expected=[{"result": None}],
        msg="$max should return null when all values reference missing fields",
    ),
    AccumulatorTestCase(
        "null_and_missing_all",
        docs=[{"v": None}, {"x": 1}],
        pipeline=_group_max("$v"),
        expected=[{"result": None}],
        msg="$max should return null when values are mix of null and missing",
    ),
    AccumulatorTestCase(
        "null_single_among_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=_group_max("$v"),
        expected=[{"result": 5}],
        msg="$max should exclude null and return max of remaining numerics",
    ),
    AccumulatorTestCase(
        "null_missing_single_among_values",
        docs=[{"x": 1}, {"v": 5}, {"v": 3}],
        pipeline=_group_max("$v"),
        expected=[{"result": 5}],
        msg="$max should exclude missing and return max of remaining numerics",
    ),
    AccumulatorTestCase(
        "null_and_missing_among_values",
        docs=[{"v": None}, {"x": 1}, {"v": 10}],
        pipeline=_group_max("$v"),
        expected=[{"result": 10}],
        msg="$max should exclude both null and missing, return max of numerics",
    ),
    AccumulatorTestCase(
        "null_one_value",
        docs=[{"v": None}, {"x": 1}, {"v": 7}],
        pipeline=_group_max("$v"),
        expected=[{"result": 7}],
        msg="$max should return the only numeric value when others are null/missing",
    ),
    AccumulatorTestCase(
        "null_two_docs",
        docs=[{"v": None}, {"x": 1}],
        pipeline=_group_max("$v"),
        expected=[{"result": None}],
        msg="$max should return null when one doc is null and one is missing",
    ),
    AccumulatorTestCase(
        "null_remove_via_cond",
        docs=[{"v": -1}, {"v": 5}, {"v": 3}],
        pipeline=_group_max({"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"result": 5}],
        msg="$max should treat $$REMOVE as missing and exclude it",
    ),
    AccumulatorTestCase(
        "null_remove_all",
        docs=[{"v": -1}, {"v": -2}],
        pipeline=_group_max({"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"result": None}],
        msg="$max should return null when all docs produce $$REMOVE",
    ),
    AccumulatorTestCase(
        "null_remove_with_values",
        docs=[{"v": -1}, {"v": 10}, {"v": -3}, {"v": 7}],
        pipeline=_group_max({"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"result": 10}],
        msg="$max should return max of remaining values after $$REMOVE exclusion",
    ),
]


# ===========================================================================
# 2. BSON Comparison Order (Cross-Type) ($group primary)
# ===========================================================================

# Property [BSON Comparison Order]: $max compares values using BSON comparison
# order when documents contain different types.
# BSON order: MinKey < Number < String < Object < Array < Binary < ObjectId
# < Boolean < Date < Timestamp < Regex < Code < MaxKey.
MAX_BSON_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_minkey_vs_number",
        docs=[{"v": MinKey()}, {"v": 5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 5}],
        msg="$max should pick number over MinKey per BSON order",
    ),
    AccumulatorTestCase(
        "bson_number_vs_string",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "hello"}],
        msg="$max should pick string over number per BSON order",
    ),
    AccumulatorTestCase(
        "bson_string_vs_object",
        docs=[{"v": "zzz"}, {"v": {"a": 1}}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"a": 1}}],
        msg="$max should pick object over string per BSON order",
    ),
    AccumulatorTestCase(
        "bson_object_vs_array",
        docs=[{"v": {"z": 99}}, {"v": [1]}],
        pipeline=_group_max("$v"),
        expected=[{"result": [1]}],
        msg="$max should pick array over object per BSON order",
    ),
    AccumulatorTestCase(
        "bson_array_vs_binary",
        docs=[{"v": [999]}, {"v": Binary(b"\x00")}],
        pipeline=_group_max("$v"),
        expected=[{"result": b"\x00"}],
        msg="$max should pick binary over array per BSON order",
    ),
    AccumulatorTestCase(
        "bson_binary_vs_objectid",
        docs=[{"v": Binary(b"\xff" * 100)}, {"v": ObjectId("000000000000000000000001")}],
        pipeline=_group_max("$v"),
        expected=[{"result": ObjectId("000000000000000000000001")}],
        msg="$max should pick ObjectId over binary per BSON order",
    ),
    AccumulatorTestCase(
        "bson_objectid_vs_boolean",
        docs=[{"v": ObjectId("ffffffffffffffffffffffff")}, {"v": False}],
        pipeline=_group_max("$v"),
        expected=[{"result": False}],
        msg="$max should pick boolean over ObjectId per BSON order",
    ),
    AccumulatorTestCase(
        "bson_boolean_vs_datetime",
        docs=[{"v": True}, {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        pipeline=_group_max("$v"),
        expected=[{"result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$max should pick datetime over boolean per BSON order",
    ),
    AccumulatorTestCase(
        "bson_datetime_vs_timestamp",
        docs=[
            {"v": datetime(9999, 12, 31, tzinfo=timezone.utc)},
            {"v": Timestamp(0, 1)},
        ],
        pipeline=_group_max("$v"),
        expected=[{"result": Timestamp(0, 1)}],
        msg="$max should pick timestamp over datetime per BSON order",
    ),
    AccumulatorTestCase(
        "bson_timestamp_vs_regex",
        docs=[{"v": Timestamp(4294967295, 4294967295)}, {"v": Regex("a")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Regex("a")}],
        msg="$max should pick regex over timestamp per BSON order",
    ),
    # NOTE: bson_regex_vs_code, bson_code_vs_maxkey, and bson_minkey_vs_maxkey
    # are stage-dependent and tested separately in the stage divergence section.
    AccumulatorTestCase(
        "bson_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=_group_max("$v"),
        expected=[{"result": False}],
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "bson_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=_group_max("$v"),
        expected=[{"result": True}],
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "bson_string_before_number",
        docs=[{"v": "a"}, {"v": 999999}],
        pipeline=_group_max("$v"),
        expected=[{"result": "a"}],
        msg="$max should pick string over number regardless of insertion order",
    ),
    # NOTE: bson_maxkey_before_minkey is stage-dependent and tested separately
    # in the stage divergence section.
]


# ===========================================================================
# 3. Within-Type Ordering ($group primary)
# ===========================================================================

# Property [Numeric Comparison]: values of the same numeric type are compared
# numerically; cross-type numeric comparisons use numeric value.

# 3a. Numeric comparison
MAX_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "numeric_int32_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=_group_max("$v"),
        expected=[{"result": 30}],
        msg="$max should return the largest int32 value",
    ),
    AccumulatorTestCase(
        "numeric_int64_basic",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        pipeline=_group_max("$v"),
        expected=[{"result": Int64(300)}],
        msg="$max should return the largest int64 value",
    ),
    AccumulatorTestCase(
        "numeric_double_basic",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 3.5}],
        msg="$max should return the largest double value",
    ),
    AccumulatorTestCase(
        "numeric_decimal128_basic",
        docs=[{"v": Decimal128("1.5")}, {"v": Decimal128("3.5")}, {"v": Decimal128("2.5")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("3.5")}],
        msg="$max should return the largest Decimal128 value",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_int64",
        docs=[{"v": 5}, {"v": Int64(10)}],
        pipeline=_group_max("$v"),
        expected=[{"result": Int64(10)}],
        msg="$max should pick Int64(10) over int32(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_double",
        docs=[{"v": 5}, {"v": 10.5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 10.5}],
        msg="$max should pick double(10.5) over int32(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_decimal",
        docs=[{"v": 5}, {"v": Decimal128("10")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("10")}],
        msg="$max should pick Decimal128(10) over int32(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_double",
        docs=[{"v": Int64(5)}, {"v": 10.5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 10.5}],
        msg="$max should pick double(10.5) over Int64(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_decimal",
        docs=[{"v": Int64(5)}, {"v": Decimal128("10")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("10")}],
        msg="$max should pick Decimal128(10) over Int64(5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_double_decimal",
        docs=[{"v": 5.5}, {"v": Decimal128("10")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("10")}],
        msg="$max should pick Decimal128(10) over double(5.5) numerically",
    ),
    AccumulatorTestCase(
        "numeric_all_four_types",
        docs=[{"v": 1}, {"v": Int64(2)}, {"v": 3.0}, {"v": Decimal128("4")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("4")}],
        msg="$max should return the numerically largest across all four numeric types",
    ),
    AccumulatorTestCase(
        "numeric_ieee754_rounding",
        docs=[{"v": 3.14}, {"v": Decimal128("3.14")}],
        pipeline=_group_max("$v"),
        expected=[{"result": 3.14}],
        msg="$max should pick double 3.14 over Decimal128 3.14 (IEEE 754 rounding)",
    ),
]

# 3b. String comparison
MAX_STRING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "abd"}],
        msg="$max should pick the lexicographically larger string",
    ),
    AccumulatorTestCase(
        "string_case",
        docs=[{"v": "a"}, {"v": "A"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "a"}],
        msg="$max should pick lowercase 'a' over uppercase 'A' (byte order)",
    ),
    AccumulatorTestCase(
        "string_digits_lexicographic",
        docs=[{"v": "9"}, {"v": "10"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "9"}],
        msg="$max should compare strings lexicographically, not numerically",
    ),
    AccumulatorTestCase(
        "string_prefix",
        docs=[{"v": "abc"}, {"v": "abcd"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "abcd"}],
        msg="$max should pick the longer string when prefix matches",
    ),
    AccumulatorTestCase(
        "string_empty_vs_nonempty",
        docs=[{"v": ""}, {"v": "a"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "a"}],
        msg="$max should pick non-empty string over empty string",
    ),
    AccumulatorTestCase(
        "string_null_byte",
        docs=[{"v": "a\x00b"}, {"v": "a\x00c"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "a\x00c"}],
        msg="$max should compare strings containing null bytes correctly",
    ),
]

# 3c. Boolean ordering
MAX_BOOLEAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boolean_true_vs_false",
        docs=[{"v": True}, {"v": False}],
        pipeline=_group_max("$v"),
        expected=[{"result": True}],
        msg="$max should pick True over False",
    ),
    AccumulatorTestCase(
        "boolean_false_vs_true",
        docs=[{"v": False}, {"v": True}],
        pipeline=_group_max("$v"),
        expected=[{"result": True}],
        msg="$max should pick True over False regardless of insertion order",
    ),
]

# 3d. Datetime ordering
MAX_DATETIME_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "datetime_chronological",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2023, 6, 15, tzinfo=timezone.utc)},
        ],
        pipeline=_group_max("$v"),
        expected=[{"result": datetime(2023, 6, 15, tzinfo=timezone.utc)}],
        msg="$max should pick the later datetime",
    ),
    AccumulatorTestCase(
        "datetime_pre_epoch_vs_epoch",
        docs=[{"v": DATE_BEFORE_EPOCH}, {"v": DATE_EPOCH}],
        pipeline=_group_max("$v"),
        expected=[{"result": DATE_EPOCH}],
        msg="$max should pick epoch over pre-epoch datetime",
    ),
    AccumulatorTestCase(
        "datetime_epoch_vs_future",
        docs=[{"v": DATE_EPOCH}, {"v": DATE_Y2K}],
        pipeline=_group_max("$v"),
        expected=[{"result": DATE_Y2K}],
        msg="$max should pick Y2K over epoch datetime",
    ),
    AccumulatorTestCase(
        "datetime_millisecond_precision",
        docs=[
            {"v": datetime(2020, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc)},
        ],
        pipeline=_group_max("$v"),
        expected=[{"result": datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc)}],
        msg="$max should distinguish datetimes by millisecond precision",
    ),
    AccumulatorTestCase(
        "datetime_boundaries",
        docs=[{"v": DATE_YEAR_1}, {"v": DATE_YEAR_9999}],
        pipeline=_group_max("$v"),
        expected=[{"result": DATE_YEAR_9999}],
        msg="$max should pick year 9999 over year 1",
    ),
]

# 3e. Timestamp ordering
MAX_TIMESTAMP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "timestamp_higher_time",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(200, 1)}],
        pipeline=_group_max("$v"),
        expected=[{"result": Timestamp(200, 1)}],
        msg="$max should pick the timestamp with higher time component",
    ),
    AccumulatorTestCase(
        "timestamp_same_time_higher_increment",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(100, 2)}],
        pipeline=_group_max("$v"),
        expected=[{"result": Timestamp(100, 2)}],
        msg="$max should pick the timestamp with higher increment on same time",
    ),
    AccumulatorTestCase(
        "timestamp_max_signed32",
        docs=[{"v": TS_EPOCH}, {"v": TS_MAX_SIGNED32}],
        pipeline=_group_max("$v"),
        expected=[{"result": TS_MAX_SIGNED32}],
        msg="$max should handle max signed 32-bit timestamp",
    ),
    AccumulatorTestCase(
        "timestamp_max_unsigned32",
        docs=[{"v": TS_MAX_SIGNED32}, {"v": TS_MAX_UNSIGNED32}],
        pipeline=_group_max("$v"),
        expected=[{"result": TS_MAX_UNSIGNED32}],
        msg="$max should handle max unsigned 32-bit timestamp",
    ),
]

# 3f. ObjectId ordering
MAX_OBJECTID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "objectid_later_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000000")},
            {"v": ObjectId("000000020000000000000000")},
        ],
        pipeline=_group_max("$v"),
        expected=[{"result": ObjectId("000000020000000000000000")}],
        msg="$max should pick the ObjectId with a later timestamp",
    ),
    AccumulatorTestCase(
        "objectid_same_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000001")},
            {"v": ObjectId("000000010000000000000002")},
        ],
        pipeline=_group_max("$v"),
        expected=[{"result": ObjectId("000000010000000000000002")}],
        msg="$max should pick the ObjectId with higher random bytes on same timestamp",
    ),
]

# 3g. Binary ordering
MAX_BINARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "binary_content",
        docs=[{"v": Binary(b"\x01")}, {"v": Binary(b"\x02")}],
        pipeline=_group_max("$v"),
        expected=[{"result": b"\x02"}],
        msg="$max should pick the binary with higher byte content",
    ),
    AccumulatorTestCase(
        "binary_subtype",
        docs=[{"v": Binary(b"\x01", 0)}, {"v": Binary(b"\x01", 5)}],
        pipeline=_group_max("$v"),
        expected=[{"result": Binary(b"\x01", 5)}],
        msg="$max should pick the binary with higher subtype on same content",
    ),
]

# 3h. Regex ordering
MAX_REGEX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "regex_pattern",
        docs=[{"v": Regex("abc", "")}, {"v": Regex("def", "")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Regex("def", "")}],
        msg="$max should pick the regex with the higher pattern string",
    ),
    AccumulatorTestCase(
        "regex_flags",
        docs=[{"v": Regex("abc", "i")}, {"v": Regex("abc", "m")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Regex("abc", "m")}],
        msg="$max should pick the regex with higher flag string on same pattern",
    ),
]

# 3i. Code ordering
# NOTE: code_basic is stage-dependent (pymongo returns Code without scope as
# str in $group/$bucket but as Code in $bucketAuto) and tested separately
# in the stage divergence section.
MAX_CODE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "code_with_scope_vs_code",
        docs=[{"v": Code("z")}, {"v": Code("a", {"x": 1})}],
        pipeline=_group_max("$v"),
        expected=[{"result": Code("a", {"x": 1})}],
        msg="$max should pick CodeWithScope over Code regardless of code string",
    ),
]

# 3j. Object (embedded document) ordering
MAX_OBJECT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "object_first_differing_field",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 3}}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"a": 1, "b": 3}}],
        msg="$max should pick object with greater value at first differing field",
    ),
    AccumulatorTestCase(
        "object_more_fields",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1, "b": 2}}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"a": 1, "b": 2}}],
        msg="$max should pick object with more fields when prefix matches",
    ),
    AccumulatorTestCase(
        "object_empty_vs_nonempty",
        docs=[{"v": {}}, {"v": {"a": 1}}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"a": 1}}],
        msg="$max should pick non-empty object over empty object",
    ),
    AccumulatorTestCase(
        "object_nested",
        docs=[{"v": {"a": {"b": 1}}}, {"v": {"a": {"b": 2}}}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"a": {"b": 2}}}],
        msg="$max should compare nested objects recursively",
    ),
]

# 3k. Array ordering (as values, NOT traversed in accumulator context)
MAX_ARRAY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "array_element_by_element",
        docs=[{"v": [1, 2, 3]}, {"v": [1, 2, 4]}],
        pipeline=_group_max("$v"),
        expected=[{"result": [1, 2, 4]}],
        msg="$max should compare arrays element by element",
    ),
    AccumulatorTestCase(
        "array_longer_prefix",
        docs=[{"v": [1, 2]}, {"v": [1, 2, 3]}],
        pipeline=_group_max("$v"),
        expected=[{"result": [1, 2, 3]}],
        msg="$max should pick longer array when prefix matches",
    ),
    AccumulatorTestCase(
        "array_empty_vs_nonempty",
        docs=[{"v": []}, {"v": [1]}],
        pipeline=_group_max("$v"),
        expected=[{"result": [1]}],
        msg="$max should pick non-empty array over empty array",
    ),
    AccumulatorTestCase(
        "array_nested",
        docs=[{"v": [[1]]}, {"v": [[2]]}],
        pipeline=_group_max("$v"),
        expected=[{"result": [[2]]}],
        msg="$max should compare nested arrays recursively",
    ),
]

WITHIN_TYPE_TESTS = (
    MAX_NUMERIC_TESTS
    + MAX_STRING_TESTS
    + MAX_BOOLEAN_TESTS
    + MAX_DATETIME_TESTS
    + MAX_TIMESTAMP_TESTS
    + MAX_OBJECTID_TESTS
    + MAX_BINARY_TESTS
    + MAX_REGEX_TESTS
    + MAX_CODE_TESTS
    + MAX_OBJECT_TESTS
    + MAX_ARRAY_TESTS
)


# ===========================================================================
# 4. NaN Handling ($group primary)
# ===========================================================================

# Property [NaN Behavior]: NaN compares as less than all other numeric values
# (including negative infinity) in BSON comparison order. As the sole value,
# NaN is returned. Decimal128 -NaN is preserved.
MAX_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_sole_float",
        docs=[{"v": FLOAT_NAN}],
        pipeline=_group_max("$v"),
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$max should return float NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_sole_decimal",
        docs=[{"v": DECIMAL128_NAN}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_NAN}],
        msg="$max should return Decimal128 NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_decimal_negative",
        docs=[{"v": DECIMAL128_NEGATIVE_NAN}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_NEGATIVE_NAN}],
        msg="$max should preserve Decimal128 -NaN as sole value",
    ),
    AccumulatorTestCase(
        "nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 5}],
        msg="$max should pick positive number over float NaN",
    ),
    AccumulatorTestCase(
        "nan_vs_negative",
        docs=[{"v": FLOAT_NAN}, {"v": -1000}],
        pipeline=_group_max("$v"),
        expected=[{"result": -1000}],
        msg="$max should pick negative number over float NaN (NaN < all numerics)",
    ),
    AccumulatorTestCase(
        "nan_vs_neg_infinity",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=_group_max("$v"),
        expected=[{"result": FLOAT_NEGATIVE_INFINITY}],
        msg="$max should pick -Infinity over float NaN",
    ),
    # NOTE: nan_float_vs_decimal is stage-dependent ($group/$bucket return
    # the last NaN type, $bucketAuto returns the first) and tested separately
    # in the stage divergence section.
    AccumulatorTestCase(
        "nan_as_only_nonnull",
        docs=[{"v": None}, {"v": FLOAT_NAN}],
        pipeline=_group_max("$v"),
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$max should return NaN when it is the only non-null value",
    ),
    AccumulatorTestCase(
        "nan_three_docs",
        docs=[{"v": FLOAT_NAN}, {"v": 5}, {"v": 10}],
        pipeline=_group_max("$v"),
        expected=[{"result": 10}],
        msg="$max should pick 10 over NaN and 5",
    ),
]


# ===========================================================================
# 5. Infinity Handling ($group primary)
# ===========================================================================

# Property [Infinity Comparison]: +Infinity > all finite values; -Infinity
# < all finite values but > NaN. String > Number in BSON order, so Infinity
# < any string.
MAX_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "inf_vs_int32",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over INT32_MAX",
    ),
    AccumulatorTestCase(
        "inf_vs_int64",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT64_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over INT64_MAX",
    ),
    AccumulatorTestCase(
        "inf_vs_double",
        docs=[{"v": FLOAT_INFINITY}, {"v": DOUBLE_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "inf_vs_decimal128",
        docs=[{"v": FLOAT_INFINITY}, {"v": DECIMAL128_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick float Infinity over DECIMAL128_MAX",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_double",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DOUBLE_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$max should pick Decimal128 Infinity over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_int32",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=_group_max("$v"),
        expected=[{"result": INT32_MIN}],
        msg="$max should pick INT32_MIN over -Infinity",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_decimal",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_MIN}],
        msg="$max should pick DECIMAL128_MIN over -Infinity",
    ),
    AccumulatorTestCase(
        "inf_vs_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=_group_max("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max should pick Infinity over -Infinity",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_neg_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_NEGATIVE_INFINITY}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$max should pick Decimal128 Infinity over Decimal128 -Infinity",
    ),
    AccumulatorTestCase(
        "inf_vs_string",
        docs=[{"v": FLOAT_INFINITY}, {"v": "hello"}],
        pipeline=_group_max("$v"),
        expected=[{"result": "hello"}],
        msg="$max should pick string over Infinity (string > number in BSON order)",
    ),
]


# ===========================================================================
# 6. Numeric Boundary Values ($group primary)
# ===========================================================================

# Property [Numeric Boundaries]: boundary values across all numeric types
# are compared correctly.
MAX_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max_vs_min",
        docs=[{"v": INT32_MAX}, {"v": INT32_MIN}],
        pipeline=_group_max("$v"),
        expected=[{"result": INT32_MAX}],
        msg="$max should pick INT32_MAX over INT32_MIN",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_vs_min",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=_group_max("$v"),
        expected=[{"result": INT64_MAX}],
        msg="$max should pick INT64_MAX over INT64_MIN",
    ),
    AccumulatorTestCase(
        "boundary_double_max_vs_min",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        pipeline=_group_max("$v"),
        expected=[{"result": DOUBLE_MAX}],
        msg="$max should pick DOUBLE_MAX over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "boundary_decimal_max_vs_min",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MIN}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_MAX}],
        msg="$max should pick DECIMAL128_MAX over DECIMAL128_MIN",
    ),
    AccumulatorTestCase(
        "boundary_int32_max_vs_int64_max",
        docs=[{"v": INT32_MAX}, {"v": INT64_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": INT64_MAX}],
        msg="$max should pick INT64_MAX over INT32_MAX",
    ),
    AccumulatorTestCase(
        "boundary_double_max_vs_int64_max",
        docs=[{"v": DOUBLE_MAX}, {"v": INT64_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": DOUBLE_MAX}],
        msg="$max should pick DOUBLE_MAX over INT64_MAX",
    ),
    AccumulatorTestCase(
        "boundary_decimal_max_vs_double_max",
        docs=[{"v": DECIMAL128_MAX}, {"v": DOUBLE_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_MAX}],
        msg="$max should pick DECIMAL128_MAX over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "boundary_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_ZERO}],
        pipeline=_group_max("$v"),
        expected=[{"result": DOUBLE_MIN_SUBNORMAL}],
        msg="$max should pick smallest positive subnormal over zero",
    ),
    AccumulatorTestCase(
        "boundary_neg_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, {"v": DOUBLE_ZERO}],
        pipeline=_group_max("$v"),
        expected=[{"result": DOUBLE_ZERO}],
        msg="$max should pick zero over negative subnormal",
    ),
    AccumulatorTestCase(
        "boundary_near_max",
        docs=[{"v": DOUBLE_NEAR_MAX}, {"v": DOUBLE_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": DOUBLE_MAX}],
        msg="$max should pick DOUBLE_MAX over DOUBLE_NEAR_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int32_adjacent",
        docs=[{"v": INT32_MAX}, {"v": INT32_MAX_MINUS_1}],
        pipeline=_group_max("$v"),
        expected=[{"result": INT32_MAX}],
        msg="$max should pick INT32_MAX over INT32_MAX - 1",
    ),
    AccumulatorTestCase(
        "boundary_int64_adjacent",
        docs=[{"v": INT64_MAX}, {"v": INT64_MAX_MINUS_1}],
        pipeline=_group_max("$v"),
        expected=[{"result": INT64_MAX}],
        msg="$max should pick INT64_MAX over INT64_MAX - 1",
    ),
]


# ===========================================================================
# 7. Negative Zero ($group primary)
# ===========================================================================

# Property [Negative Zero]: -0.0 and +0.0 are numerically equal; tie-breaking
# by document order differs by stage ($group/$bucket: last wins, $bucketAuto:
# first wins). The stage-dependent tie tests are in the divergence section.
MAX_NEGZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_vs_positive",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": 1}],
        pipeline=_group_max("$v"),
        expected=[{"result": 1}],
        msg="$max should pick positive number over double -0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_vs_positive",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": 1.0}],
        pipeline=_group_max("$v"),
        expected=[{"result": 1.0}],
        msg="$max should pick positive number over Decimal128 -0",
    ),
]


# ===========================================================================
# 8. Decimal128 Precision ($group primary)
# ===========================================================================

# Property [Decimal128 Precision]: Decimal128 precision boundaries are
# handled correctly.
MAX_DECIMAL_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_high_precision",
        docs=[
            {"v": Decimal128("1.234567890123456789012345678901234")},
            {"v": Decimal128("1.234567890123456789012345678901235")},
        ],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("1.234567890123456789012345678901235")}],
        msg="$max should distinguish 34-digit Decimal128 values",
    ),
    # NOTE: decimal_trailing_zeros is stage-dependent ($group/$bucket return
    # the last equal value, $bucketAuto returns the first) and tested separately
    # in the stage divergence section.
    AccumulatorTestCase(
        "decimal_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_MAX}],
        msg="$max should pick DECIMAL128_MAX over DECIMAL128_LARGE_EXPONENT",
    ),
    AccumulatorTestCase(
        "decimal_min_positive",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_MIN_POSITIVE}],
        msg="$max should pick DECIMAL128_MIN_POSITIVE over zero",
    ),
    AccumulatorTestCase(
        "decimal_max_negative",
        docs=[{"v": DECIMAL128_MAX_NEGATIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_ZERO}],
        msg="$max should pick zero over DECIMAL128_MAX_NEGATIVE",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_max",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_MAX}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_INFINITY}],
        msg="$max should pick Decimal128 Infinity over DECIMAL128_MAX",
    ),
    AccumulatorTestCase(
        "decimal_neg_inf_vs_min",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_MIN}],
        msg="$max should pick DECIMAL128_MIN over Decimal128 -Infinity",
    ),
    AccumulatorTestCase(
        "decimal_nan_vs_finite",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("5")}],
        msg="$max should pick finite Decimal128 over Decimal128 NaN",
    ),
]


# ===========================================================================
# 9. BSON Type Distinction ($group primary)
# ===========================================================================

# Property [BSON Type Distinction]: values of different BSON types are
# distinct even when they appear similar.
MAX_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=_group_max("$v"),
        expected=[{"result": False}],
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=_group_max("$v"),
        expected=[{"result": True}],
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        pipeline=_group_max("$v"),
        expected=[{"result": ""}],
        msg="$max should exclude null and return empty string",
    ),
    AccumulatorTestCase(
        "distinct_numeric_string",
        docs=[{"v": "123"}, {"v": 1000000}],
        pipeline=_group_max("$v"),
        expected=[{"result": "123"}],
        msg="$max should pick string '123' over int 1000000 (string > number, no coercion)",
    ),
]


# ===========================================================================
# 10. Expression Argument Tests ($group primary)
# ===========================================================================

# Property [Input Forms]: $max accumulator accepts various expression types
# as its operand.
MAX_INPUT_FORM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "input_field_path",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 20}],
        msg="$max should accept a basic field path reference",
    ),
    AccumulatorTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 20}}, {"a": {"b": 5}}],
        pipeline=_group_max("$a.b"),
        expected=[{"result": 20}],
        msg="$max should accept a nested document field path",
    ),
    AccumulatorTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=_group_max(42),
        expected=[{"result": 42}],
        msg="$max with a literal constant should return that constant",
    ),
    AccumulatorTestCase(
        "input_expression",
        docs=[{"price": 10, "qty": 2}, {"price": 5, "qty": 10}],
        pipeline=_group_max({"$multiply": ["$price", "$qty"]}),
        expected=[{"result": 50}],
        msg="$max should accept a computed expression as operand",
    ),
    AccumulatorTestCase(
        "input_cond_remove",
        docs=[{"v": -1}, {"v": 5}, {"v": 3}],
        pipeline=_group_max({"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"result": 5}],
        msg="$max should accept conditional with $$REMOVE as operand",
    ),
    AccumulatorTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=_group_max(None),
        expected=[{"result": None}],
        msg="$max with null literal should return null (all docs produce null)",
    ),
]


# ===========================================================================
# 11. Accumulator-Specific Edge Cases ($group primary)
# ===========================================================================

# Property [Edge Cases]: edge cases unique to accumulator context.
MAX_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        pipeline=_group_max("$v"),
        expected=[{"result": 42}],
        msg="$max of a single document should return that document's value",
    ),
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=_group_max("$v"),
        expected=[{"result": None}],
        msg="$max of a single null document should return null",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=_group_max("$v"),
        expected=[{"result": None}],
        msg="$max of a single document with missing field should return null",
    ),
    AccumulatorTestCase(
        "edge_multi_group",
        docs=[
            {"g": "A", "v": 10},
            {"g": "A", "v": 20},
            {"g": "B", "v": 5},
            {"g": "B", "v": 15},
        ],
        pipeline=_group_max("$v"),
        expected=[{"result": 20}],
        msg="$max should compute correctly across documents (single group via $literal)",
    ),
    AccumulatorTestCase(
        "edge_many_docs",
        docs=[{"v": i} for i in range(100)],
        pipeline=_group_max("$v"),
        expected=[{"result": 99}],
        msg="$max should return correct value across 100 documents",
    ),
    AccumulatorTestCase(
        "edge_array_field_not_traversed",
        docs=[{"v": [5, 1, 8]}, {"v": [3, 9, 2]}],
        pipeline=_group_max("$v"),
        expected=[{"result": [5, 1, 8]}],
        msg="$max should compare arrays as whole values, not traverse them",
    ),
    AccumulatorTestCase(
        "edge_mixed_array_scalar",
        docs=[{"v": [1, 2, 3]}, {"v": 5}],
        pipeline=_group_max("$v"),
        expected=[{"result": [1, 2, 3]}],
        msg="$max should pick array over scalar (array > number in BSON order)",
    ),
]


# ===========================================================================
# Combine all $group primary success tests
# ===========================================================================

MAX_GROUP_SUCCESS_TESTS = (
    MAX_NULL_MISSING_TESTS
    + MAX_BSON_ORDER_TESTS
    + WITHIN_TYPE_TESTS
    + MAX_NAN_TESTS
    + MAX_INFINITY_TESTS
    + MAX_BOUNDARY_TESTS
    + MAX_NEGZERO_TESTS
    + MAX_DECIMAL_PRECISION_TESTS
    + MAX_TYPE_DISTINCTION_TESTS
    + MAX_INPUT_FORM_TESTS
    + MAX_EDGE_CASE_TESTS
)


# ===========================================================================
# $group primary test function
# ===========================================================================


@pytest.mark.parametrize("test_case", pytest_params(MAX_GROUP_SUCCESS_TESTS))
def test_accumulator_max_group(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator success cases via $group."""
    result = _run(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# ===========================================================================
# 12. $bucket Smoke Tests
# ===========================================================================

# Property [Bucket Stage Smoke]: $max produces correct results through $bucket
# for representative cases from each property category.
MAX_BUCKET_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=_bucket_max("$v"),
        expected=[{"result": None}],
        msg="$max via $bucket should return null when all values are null",
    ),
    AccumulatorTestCase(
        "bucket_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=_bucket_max("$v"),
        expected=[{"result": 30}],
        msg="$max via $bucket should return the largest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=_bucket_max("$v"),
        expected=[{"result": "abd"}],
        msg="$max via $bucket should pick the lexicographically larger string",
    ),
    AccumulatorTestCase(
        "bucket_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 5}],
        pipeline=_bucket_max("$v"),
        expected=[{"result": 5}],
        msg="$max via $bucket should pick positive number over NaN",
    ),
    AccumulatorTestCase(
        "bucket_infinity",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MAX}],
        pipeline=_bucket_max("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max via $bucket should pick Infinity over INT32_MAX",
    ),
    AccumulatorTestCase(
        "bucket_boundary_int64",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=_bucket_max("$v"),
        expected=[{"result": INT64_MAX}],
        msg="$max via $bucket should pick INT64_MAX over INT64_MIN",
    ),
    AccumulatorTestCase(
        "bucket_edge_single_doc",
        docs=[{"v": 42}],
        pipeline=_bucket_max("$v"),
        expected=[{"result": 42}],
        msg="$max via $bucket should handle single document",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_BUCKET_SMOKE_TESTS))
def test_accumulator_max_bucket(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator via $bucket for representative cases."""
    result = _run(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# ===========================================================================
# 13. $bucketAuto Smoke Tests
# ===========================================================================

# Property [BucketAuto Stage Smoke]: $max produces correct results through
# $bucketAuto for representative cases from each property category.
MAX_BUCKET_AUTO_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": None}],
        msg="$max via $bucketAuto should return null when all values are null",
    ),
    AccumulatorTestCase(
        "bucket_auto_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 30}],
        msg="$max via $bucketAuto should return the largest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_auto_string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": "abd"}],
        msg="$max via $bucketAuto should pick the lexicographically larger string",
    ),
    AccumulatorTestCase(
        "bucket_auto_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 5}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 5}],
        msg="$max via $bucketAuto should pick positive number over NaN",
    ),
    AccumulatorTestCase(
        "bucket_auto_infinity",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MAX}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max via $bucketAuto should pick Infinity over INT32_MAX",
    ),
    AccumulatorTestCase(
        "bucket_auto_boundary_int64",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": INT64_MAX}],
        msg="$max via $bucketAuto should pick INT64_MAX over INT64_MIN",
    ),
    AccumulatorTestCase(
        "bucket_auto_edge_single_doc",
        docs=[{"v": 42}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 42}],
        msg="$max via $bucketAuto should handle single document",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_BUCKET_AUTO_SMOKE_TESTS))
def test_accumulator_max_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator via $bucketAuto for representative cases."""
    result = _run(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# ===========================================================================
# 14. Stage Divergence Tests
# ===========================================================================
# Tests where $group/$bucket and $bucketAuto produce different results.

# ---------------------------------------------------------------------------
# 14a. BSON Order Stage Divergence
# ---------------------------------------------------------------------------

# Property [BSON Order Stage Divergence]: Code and MaxKey serialization
# differs between $group/$bucket (Code as str, MaxKey wrapped in dict) and
# $bucketAuto (Code as Code object, MaxKey as MaxKey()).
MAX_BSON_ORDER_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_group",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=_group_max("$v"),
        expected=[{"result": "a"}],
        msg="$max should pick Code over regex per BSON order (returned as str in $group)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_group",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"": MaxKey()}}],
        msg="$max should pick MaxKey over Code per BSON order (wrapped in dict in $group)",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_group",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"": MaxKey()}}],
        msg="$max should pick MaxKey over MinKey (wrapped in dict in $group)",
    ),
    AccumulatorTestCase(
        "bson_maxkey_before_minkey_group",
        docs=[{"v": MaxKey()}, {"v": MinKey()}],
        pipeline=_group_max("$v"),
        expected=[{"result": {"": MaxKey()}}],
        msg="$max should pick MaxKey even when first (wrapped in dict in $group)",
    ),
]

MAX_BSON_ORDER_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_bucket_auto",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": Code("a")}],
        msg="$max should pick Code over regex per BSON order in $bucketAuto",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_bucket_auto",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": MaxKey()}],
        msg="$max should pick MaxKey over Code per BSON order in $bucketAuto",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_bucket_auto",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": MaxKey()}],
        msg="$max should pick MaxKey over MinKey in $bucketAuto",
    ),
    AccumulatorTestCase(
        "bson_maxkey_before_minkey_bucket_auto",
        docs=[{"v": MaxKey()}, {"v": MinKey()}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": MaxKey()}],
        msg="$max should pick MaxKey even when first in $bucketAuto",
    ),
]

# ---------------------------------------------------------------------------
# 14b. Code Ordering Stage Divergence
# ---------------------------------------------------------------------------

# Property [Code Ordering Stage Divergence]: pymongo returns Code without
# scope as str in $group/$bucket but as Code in $bucketAuto.
MAX_CODE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "code_basic_group",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=_group_max("$v"),
        expected=[{"result": "b()"}],
        msg="$max should pick Code with higher string value (returned as str in $group)",
    ),
]

MAX_CODE_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "code_basic_bucket_auto",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": Code("b()")}],
        msg="$max should pick Code with higher string value in $bucketAuto",
    ),
]

# ---------------------------------------------------------------------------
# 14c. NaN Tie-Breaking Stage Divergence
# ---------------------------------------------------------------------------

# Property [NaN Tie-Breaking Stage Divergence]: $group/$bucket return last
# NaN type, $bucketAuto returns first.
MAX_NAN_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_group",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_NAN}],
        msg="$max should return last NaN type (Decimal128 NaN) in $group",
    ),
]

MAX_NAN_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_bucket_auto",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$max should return first NaN type (float NaN) in $bucketAuto",
    ),
]

# ---------------------------------------------------------------------------
# 14d. Negative Zero Tie-Breaking Stage Divergence
# ---------------------------------------------------------------------------

# Property [Negative Zero Tie-Breaking Stage Divergence]: $group/$bucket
# return last (positive zero), $bucketAuto returns first (negative zero).
MAX_NEGZERO_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_group",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_ZERO}],
        pipeline=_group_max("$v"),
        expected=[{"result": DOUBLE_ZERO}],
        msg="$max should return last zero (positive) when -0.0 and 0.0 tie in $group",
    ),
    AccumulatorTestCase(
        "negzero_decimal_group",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_ZERO}],
        msg="$max should return last zero (positive) when Decimal128 -0 and 0 tie in $group",
    ),
]

MAX_NEGZERO_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_bucket_auto",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_ZERO}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": DOUBLE_NEGATIVE_ZERO}],
        msg="$max should return first zero (-0.0) when -0.0 and 0.0 tie in $bucketAuto",
    ),
    AccumulatorTestCase(
        "negzero_decimal_bucket_auto",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": DECIMAL128_NEGATIVE_ZERO}],
        msg="$max should return first zero (Decimal128 -0) when -0 and 0 tie in $bucketAuto",
    ),
]

# ---------------------------------------------------------------------------
# 14e. Decimal Trailing Zeros Stage Divergence
# ---------------------------------------------------------------------------

# Property [Decimal Trailing Zeros Stage Divergence]: $group/$bucket return
# last, $bucketAuto returns first.
MAX_DECIMAL_TRAILING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_group",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("1.00")}],
        msg="$max should return last Decimal128 (1.00) when equal in $group",
    ),
]

MAX_DECIMAL_TRAILING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_bucket_auto",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": Decimal128("1.0")}],
        msg="$max should return first Decimal128 (1.0) when equal in $bucketAuto",
    ),
]

# ---------------------------------------------------------------------------
# 14f. Tie-Breaking Stage Divergence
# ---------------------------------------------------------------------------

# Property [Tie-Breaking Stage Divergence]: when values are numerically equal
# but different types, $group/$bucket preserve the last encountered type while
# $bucketAuto preserves the first.
MAX_TIE_BREAKING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_group",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=_group_max("$v"),
        expected=[{"result": Int64(5)}],
        msg="$max should preserve type of last equal value (Int64) in $group",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_group",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 5}],
        msg="$max should preserve type of last equal value (int32) in $group",
    ),
    AccumulatorTestCase(
        "tie_double_int32_group",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 5}],
        msg="$max should preserve type of last equal value (int32) in $group",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_group",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=_group_max("$v"),
        expected=[{"result": Int64(5)}],
        msg="$max should preserve type of last equal value (Int64) in $group",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_group",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("5")}],
        msg="$max should preserve type of last equal value (Decimal128) in $group",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_group",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=_group_max("$v"),
        expected=[{"result": 5}],
        msg="$max should preserve type of last equal value (int32) in $group",
    ),
]

MAX_TIE_BREAKING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 5}],
        msg="$max should preserve type of first equal value (int32) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_bucket_auto",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": Int64(5)}],
        msg="$max should preserve type of first equal value (Int64) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_double_int32_bucket_auto",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 5.0}],
        msg="$max should preserve type of first equal value (double) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": Decimal128("5")}],
        msg="$max should preserve type of first equal value (Decimal128) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 5}],
        msg="$max should preserve type of first equal value (int32) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": Decimal128("5")}],
        msg="$max should preserve type of first equal value (Decimal128) in $bucketAuto",
    ),
]

# ---------------------------------------------------------------------------
# 14g. Numeric Equivalence Stage Divergence
# ---------------------------------------------------------------------------

# Property [Numeric Equivalence Stage Divergence]: numerically equivalent
# values across types are treated as equal; tie-breaking differs by stage.
MAX_NUMERIC_EQUIV_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_int_long_double_decimal_group",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=_group_max("$v"),
        expected=[{"result": Decimal128("5")}],
        msg="$max should return last type (Decimal128) for equal values in $group",
    ),
    AccumulatorTestCase(
        "equiv_zeros_group",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": DOUBLE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_max("$v"),
        expected=[{"result": DECIMAL128_ZERO}],
        msg="$max should return last type (Decimal128) for zero values in $group",
    ),
]

MAX_NUMERIC_EQUIV_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_int_long_double_decimal_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 5}],
        msg="$max should return first type (int32) for equal values in $bucketAuto",
    ),
    AccumulatorTestCase(
        "equiv_zeros_bucket_auto",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": DOUBLE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=_bucket_auto_max("$v"),
        expected=[{"result": 0}],
        msg="$max should return first type (int32) for zero values in $bucketAuto",
    ),
]

# Combine all stage divergence tests
MAX_STAGE_DIVERGENCE_TESTS = (
    MAX_BSON_ORDER_GROUP_TESTS
    + MAX_BSON_ORDER_BUCKET_AUTO_TESTS
    + MAX_CODE_GROUP_TESTS
    + MAX_CODE_BUCKET_AUTO_TESTS
    + MAX_NAN_GROUP_TESTS
    + MAX_NAN_BUCKET_AUTO_TESTS
    + MAX_NEGZERO_GROUP_TESTS
    + MAX_NEGZERO_BUCKET_AUTO_TESTS
    + MAX_DECIMAL_TRAILING_GROUP_TESTS
    + MAX_DECIMAL_TRAILING_BUCKET_AUTO_TESTS
    + MAX_TIE_BREAKING_GROUP_TESTS
    + MAX_TIE_BREAKING_BUCKET_AUTO_TESTS
    + MAX_NUMERIC_EQUIV_GROUP_TESTS
    + MAX_NUMERIC_EQUIV_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_STAGE_DIVERGENCE_TESTS))
def test_accumulator_max_stage_divergence(collection, test_case: AccumulatorTestCase):
    """Test $max cases where behavior differs between stages."""
    result = _run(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# ===========================================================================
# 15. Expression Error Propagation
# ===========================================================================

# Property [Expression Error Propagation]: errors in sub-expressions used as
# $max operand propagate as errors.

# Errors that share the same error code across all stages
MAX_EXPRESSION_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid_group",
        docs=[{"v": "not_a_number"}],
        pipeline=_group_max({"$toInt": "$v"}),
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$max should propagate conversion error from $toInt sub-expression in $group",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_group",
        docs=[{"v": 10}],
        pipeline=_group_max({"$divide": ["$v", 0]}),
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$max should propagate divide-by-zero error in $group",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_group",
        docs=[{"v": 10}],
        pipeline=_group_max({"$mod": ["$v", 0]}),
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$max should propagate mod-by-zero error in $group",
    ),
]

MAX_EXPRESSION_ERROR_BUCKET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid_bucket",
        docs=[{"v": "not_a_number"}],
        pipeline=_bucket_max({"$toInt": "$v"}),
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$max should propagate conversion error from $toInt sub-expression in $bucket",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_bucket",
        docs=[{"v": 10}],
        pipeline=_bucket_max({"$divide": ["$v", 0]}),
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$max should propagate divide-by-zero error in $bucket",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_bucket",
        docs=[{"v": 10}],
        pipeline=_bucket_max({"$mod": ["$v", 0]}),
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$max should propagate mod-by-zero error in $bucket",
    ),
]

# $bucketAuto wraps divide-by-zero and mod-by-zero differently
MAX_EXPRESSION_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid_bucket_auto",
        docs=[{"v": "not_a_number"}],
        pipeline=_bucket_auto_max({"$toInt": "$v"}),
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$max should propagate conversion error from $toInt in $bucketAuto",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=_bucket_auto_max({"$divide": ["$v", 0]}),
        error_code=BAD_VALUE_ERROR,
        msg="$max should propagate divide-by-zero error in $bucketAuto (wrapped as BAD_VALUE)",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=_bucket_auto_max({"$mod": ["$v", 0]}),
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="$max should propagate mod-by-zero error in $bucketAuto (wrapped as 16610)",
    ),
]

MAX_EXPRESSION_ERROR_TESTS = (
    MAX_EXPRESSION_ERROR_GROUP_TESTS
    + MAX_EXPRESSION_ERROR_BUCKET_TESTS
    + MAX_EXPRESSION_ERROR_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_EXPRESSION_ERROR_TESTS))
def test_accumulator_max_expression_errors(collection, test_case):
    """Test $max expression error propagation."""
    result = _run(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


# ===========================================================================
# 16. Arity Rejection
# ===========================================================================

# Property [Arity]: $max in accumulator context is a unary operator and
# rejects array syntax in $group, $bucket, and $bucketAuto.
MAX_ARITY_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_group",
        docs=[{"v": 1}],
        pipeline=_group_max([]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_group",
        docs=[{"v": 1}],
        pipeline=_group_max([1]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_group",
        docs=[{"v": 1}],
        pipeline=_group_max(["$v"]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_group",
        docs=[{"v": 1}],
        pipeline=_group_max([1, 2, 3]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_group",
        docs=[{"v": 1}],
        pipeline=_group_max({"$add": [1, 2], "$multiply": [3, 4]}),
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($group)",
    ),
]

MAX_ARITY_ERROR_BUCKET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_bucket",
        docs=[{"v": 1}],
        pipeline=_bucket_max([]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_bucket",
        docs=[{"v": 1}],
        pipeline=_bucket_max([1]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_bucket",
        docs=[{"v": 1}],
        pipeline=_bucket_max(["$v"]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket",
        docs=[{"v": 1}],
        pipeline=_bucket_max([1, 2, 3]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_bucket",
        docs=[{"v": 1}],
        pipeline=_bucket_max({"$add": [1, 2], "$multiply": [3, 4]}),
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($bucket)",
    ),
]

MAX_ARITY_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=_bucket_auto_max([]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=_bucket_auto_max([1]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=_bucket_auto_max(["$v"]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=_bucket_auto_max([1, 2, 3]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_bucket_auto",
        docs=[{"v": 1}],
        pipeline=_bucket_auto_max({"$add": [1, 2], "$multiply": [3, 4]}),
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($bucketAuto)",
    ),
]

MAX_ARITY_ERROR_TESTS = (
    MAX_ARITY_ERROR_GROUP_TESTS + MAX_ARITY_ERROR_BUCKET_TESTS + MAX_ARITY_ERROR_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_ARITY_ERROR_TESTS))
def test_accumulator_max_arity_errors(collection, test_case):
    """Test $max arity rejection across all three stages."""
    result = _run(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


# ===========================================================================
# 17. Return Type Verification ($group primary)
# ===========================================================================

# Property [Return Type]: $max preserves the BSON type of the maximum value.
MAX_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_int32",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": 30, "type": "int"}],
        msg="$max of int32 values should return type 'int'",
    ),
    AccumulatorTestCase(
        "return_type_int64",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": Int64(300), "type": "long"}],
        msg="$max of int64 values should return type 'long'",
    ),
    AccumulatorTestCase(
        "return_type_double",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": 3.5, "type": "double"}],
        msg="$max of double values should return type 'double'",
    ),
    AccumulatorTestCase(
        "return_type_decimal",
        docs=[{"v": Decimal128("1")}, {"v": Decimal128("3")}, {"v": Decimal128("2")}],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": Decimal128("3"), "type": "decimal"}],
        msg="$max of Decimal128 values should return type 'decimal'",
    ),
    AccumulatorTestCase(
        "return_type_string",
        docs=[{"v": "a"}, {"v": "c"}, {"v": "b"}],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": "c", "type": "string"}],
        msg="$max of string values should return type 'string'",
    ),
    AccumulatorTestCase(
        "return_type_boolean",
        docs=[{"v": True}, {"v": False}],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": True, "type": "bool"}],
        msg="$max of boolean values should return type 'bool'",
    ),
    AccumulatorTestCase(
        "return_type_date",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": datetime(2023, 1, 1, tzinfo=timezone.utc), "type": "date"}],
        msg="$max of datetime values should return type 'date'",
    ),
    AccumulatorTestCase(
        "return_type_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=_group_max_with_type("$v"),
        expected=[{"value": None, "type": "null"}],
        msg="$max of all null values should return type 'null'",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_RETURN_TYPE_TESTS))
def test_accumulator_max_return_type(collection, test_case: AccumulatorTestCase):
    """Test $max return type preservation."""
    result = _run(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)
