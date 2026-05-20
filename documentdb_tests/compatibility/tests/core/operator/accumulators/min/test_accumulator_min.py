"""Tests for $min accumulator operator."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    TS_EPOCH,
    TS_MAX_UNSIGNED32,
)


def _group_min(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline for $min."""
    return [{"$group": {"_id": None, "result": {"$min": accumulator}}}]


def _bucket_min(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $bucket pipeline for $min."""
    return [
        {
            "$bucket": {
                "groupBy": {"$literal": 0},
                "boundaries": [-1, 1],
                "output": {"result": {"$min": accumulator}},
            }
        }
    ]


def _bucket_auto_min(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $bucketAuto pipeline for $min."""
    return [
        {
            "$bucketAuto": {
                "groupBy": {"$literal": 0},
                "buckets": 1,
                "output": {"result": {"$min": accumulator}},
            }
        }
    ]


# ---------------------------------------------------------------------------
# Property lists — categories 1-16, all using $group as the primary stage
# ---------------------------------------------------------------------------

# Property [Null and Missing Ignored]: null values, missing fields, and $$REMOVE
# are excluded from the min computation. When no non-null/non-missing values
# remain, the result is null.
MIN_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}, {"v": None}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all values are null",
    ),
    AccumulatorTestCase(
        "missing_all",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all documents have missing field",
    ),
    AccumulatorTestCase(
        "null_and_missing_all",
        docs=[{"v": None}, {"x": 1}, {"v": None}, {"x": 2}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all values are null or missing",
    ),
    AccumulatorTestCase(
        "null_single_among_values",
        docs=[{"v": 10}, {"v": None}, {"v": 20}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should exclude null and return min of remaining values",
    ),
    AccumulatorTestCase(
        "missing_single_among_values",
        docs=[{"v": 10}, {"x": 1}, {"v": 20}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should exclude missing and return min of remaining values",
    ),
    AccumulatorTestCase(
        "null_and_missing_among_values",
        docs=[{"v": 10}, {"v": None}, {"x": 1}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should exclude both null and missing from computation",
    ),
    AccumulatorTestCase(
        "null_one_value",
        docs=[{"v": None}, {"x": 1}, {"v": 42}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 42}],
        msg="$min should return the only non-null/non-missing value",
    ),
    AccumulatorTestCase(
        "null_two_docs",
        docs=[{"v": None}, {"x": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when only null and missing present",
    ),
    AccumulatorTestCase(
        "remove_via_cond",
        docs=[{"v": -1}, {"v": 5}, {"v": -2}, {"v": 10}],
        pipeline=_group_min({"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"_id": None, "result": 5}],
        msg="$min should treat $$REMOVE as missing and exclude it",
    ),
    AccumulatorTestCase(
        "remove_all",
        docs=[{"v": -1}, {"v": -2}, {"v": -3}],
        pipeline=_group_min({"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when all docs produce $$REMOVE",
    ),
    AccumulatorTestCase(
        "remove_with_values",
        docs=[{"v": -1}, {"v": 5}, {"v": -2}, {"v": 3}],
        pipeline=_group_min({"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"_id": None, "result": 3}],
        msg="$min should return min of non-removed values",
    ),
]

# Property [BSON Comparison Order]: $min compares values using BSON comparison
# order when documents contain different types. BSON order:
# MinKey < Number < String < Object < Array < Binary < ObjectId < Boolean
# < Date < Timestamp < Regex < Code < MaxKey.
MIN_BSON_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_minkey_vs_number",
        docs=[{"v": MinKey()}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": MinKey()}],
        msg="$min should pick MinKey over Number (MinKey < Number)",
    ),
    AccumulatorTestCase(
        "bson_number_vs_string",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 100}],
        msg="$min should pick Number over String (Number < String)",
    ),
    AccumulatorTestCase(
        "bson_string_vs_object",
        docs=[{"v": "zzz"}, {"v": {"a": 1}}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "zzz"}],
        msg="$min should pick String over Object (String < Object)",
    ),
    AccumulatorTestCase(
        "bson_object_vs_array",
        docs=[{"v": {"z": 99}}, {"v": [1]}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": {"z": 99}}],
        msg="$min should pick Object over Array (Object < Array)",
    ),
    AccumulatorTestCase(
        "bson_array_vs_binary",
        docs=[{"v": [999]}, {"v": Binary(b"\x00")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": [999]}],
        msg="$min should pick Array over Binary (Array < Binary)",
    ),
    AccumulatorTestCase(
        "bson_binary_vs_objectid",
        docs=[{"v": Binary(b"\xff" * 100)}, {"v": ObjectId("000000000000000000000001")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": b"\xff" * 100}],
        msg="$min should pick Binary over ObjectId (Binary < ObjectId)",
    ),
    AccumulatorTestCase(
        "bson_objectid_vs_boolean",
        docs=[{"v": ObjectId("ffffffffffffffffffffffff")}, {"v": False}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": ObjectId("ffffffffffffffffffffffff")}],
        msg="$min should pick ObjectId over Boolean (ObjectId < Boolean)",
    ),
    AccumulatorTestCase(
        "bson_boolean_vs_datetime",
        docs=[{"v": True}, {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": True}],
        msg="$min should pick Boolean over Date (Boolean < Date)",
    ),
    AccumulatorTestCase(
        "bson_datetime_vs_timestamp",
        docs=[
            {"v": datetime(9999, 12, 31, tzinfo=timezone.utc)},
            {"v": Timestamp(0, 1)},
        ],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": datetime(9999, 12, 31, tzinfo=timezone.utc)}],
        msg="$min should pick Date over Timestamp (Date < Timestamp)",
    ),
    AccumulatorTestCase(
        "bson_timestamp_vs_regex",
        docs=[{"v": Timestamp(4294967295, 4294967295)}, {"v": Regex("a")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Timestamp(4294967295, 4294967295)}],
        msg="$min should pick Timestamp over Regex (Timestamp < Regex)",
    ),
    AccumulatorTestCase(
        "bson_regex_vs_code",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Regex("zzz")}],
        msg="$min should pick Regex over Code (Regex < Code)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Code("zzz")}],
        msg="$min should pick Code over MaxKey (Code < MaxKey)",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": MinKey()}],
        msg="$min should pick MinKey over MaxKey (full BSON range)",
    ),
    AccumulatorTestCase(
        "bson_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 0}],
        msg="$min should pick Number(0) over Boolean(false) (Number < Boolean)",
    ),
    AccumulatorTestCase(
        "bson_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 1}],
        msg="$min should pick Number(1) over Boolean(true) (Number < Boolean)",
    ),
    AccumulatorTestCase(
        "bson_string_before_number",
        docs=[{"v": "hello"}, {"v": 100}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 100}],
        msg="$min should pick Number regardless of document order",
    ),
    AccumulatorTestCase(
        "bson_minkey_before_maxkey",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": MinKey()}],
        msg="$min should pick MinKey regardless of document order",
    ),
]

# Property [Within-Type Ordering — Numeric]: values of the same numeric type
# follow standard numeric ordering. $min picks the smallest value.
MIN_NUMERIC_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "numeric_int32_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 10}],
        msg="$min should return smallest int32 value",
    ),
    AccumulatorTestCase(
        "numeric_int64_basic",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Int64(100)}],
        msg="$min should return smallest int64 value",
    ),
    AccumulatorTestCase(
        "numeric_double_basic",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 1.5}],
        msg="$min should return smallest double value",
    ),
    AccumulatorTestCase(
        "numeric_decimal128_basic",
        docs=[{"v": Decimal128("1.5")}, {"v": Decimal128("3.5")}, {"v": Decimal128("2.5")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("1.5")}],
        msg="$min should return smallest Decimal128 value",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_int64",
        docs=[{"v": 10}, {"v": Int64(5)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Int64(5)}],
        msg="$min should compare int32 and int64 numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_double",
        docs=[{"v": 10}, {"v": 5.5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5.5}],
        msg="$min should compare int32 and double numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_decimal",
        docs=[{"v": 10}, {"v": Decimal128("5")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("5")}],
        msg="$min should compare int32 and Decimal128 numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_double",
        docs=[{"v": Int64(10)}, {"v": 5.5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5.5}],
        msg="$min should compare int64 and double numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_decimal",
        docs=[{"v": Int64(10)}, {"v": Decimal128("5")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("5")}],
        msg="$min should compare int64 and Decimal128 numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_double_decimal",
        docs=[{"v": 10.5}, {"v": Decimal128("5")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("5")}],
        msg="$min should compare double and Decimal128 numerically",
    ),
    AccumulatorTestCase(
        "numeric_all_four_types",
        docs=[{"v": 4}, {"v": Int64(3)}, {"v": 2.0}, {"v": Decimal128("1")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("1")}],
        msg="$min should pick smallest across all four numeric types",
    ),
    AccumulatorTestCase(
        "numeric_ieee754_rounding",
        docs=[{"v": 3.14}, {"v": Decimal128("3.14")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("3.14")}],
        msg="$min should pick Decimal128('3.14') over double 3.14 due to IEEE 754 rounding",
    ),
]

# Property [Within-Type Ordering — String]: strings are compared by byte value.
MIN_STRING_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "abc"}],
        msg="$min should pick lexicographically smaller string",
    ),
    AccumulatorTestCase(
        "string_case",
        docs=[{"v": "a"}, {"v": "A"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "A"}],
        msg="$min should pick uppercase over lowercase (byte value comparison)",
    ),
    AccumulatorTestCase(
        "string_unicode_no_normalization",
        docs=[{"v": "\u00e9"}, {"v": "\u0065\u0301"}],  # precomposed vs decomposed e-acute
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "\u0065\u0301"}],
        msg="$min should distinguish precomposed and decomposed Unicode (no normalization)",
    ),
    AccumulatorTestCase(
        "string_digits_lexicographic",
        docs=[{"v": "9"}, {"v": "10"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "10"}],
        msg="$min should compare digit strings lexicographically ('1' < '9')",
    ),
    AccumulatorTestCase(
        "string_null_byte",
        docs=[{"v": "a\x00b"}, {"v": "a\x00c"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "a\x00b"}],
        msg="$min should compare strings with embedded null bytes by byte value",
    ),
    AccumulatorTestCase(
        "string_prefix",
        docs=[{"v": "abc"}, {"v": "abcd"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "abc"}],
        msg="$min should pick shorter string when it is a prefix of the longer",
    ),
    AccumulatorTestCase(
        "string_empty_vs_nonempty",
        docs=[{"v": ""}, {"v": "a"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": ""}],
        msg="$min should pick empty string over non-empty",
    ),
    AccumulatorTestCase(
        "string_4byte_utf8",
        docs=[{"v": "\U0001f600"}, {"v": "\U0001f601"}],  # emoji comparison
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": "\U0001f600"}],
        msg="$min should compare 4-byte UTF-8 characters by byte value",
    ),
]

# Property [Within-Type Ordering — Boolean]: False < True.
MIN_BOOLEAN_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boolean_true_vs_false",
        docs=[{"v": True}, {"v": False}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": False}],
        msg="$min should pick False over True",
    ),
    AccumulatorTestCase(
        "boolean_false_vs_true",
        docs=[{"v": False}, {"v": True}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": False}],
        msg="$min should pick False regardless of document order",
    ),
]

# Property [Within-Type Ordering — Datetime]: earlier datetimes are smaller.
MIN_DATETIME_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "datetime_chronological",
        docs=[
            {"v": datetime(2020, 6, 15, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$min should pick earlier datetime",
    ),
    AccumulatorTestCase(
        "datetime_pre_epoch_vs_epoch",
        docs=[{"v": DATE_BEFORE_EPOCH}, {"v": DATE_EPOCH}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DATE_BEFORE_EPOCH}],
        msg="$min should pick pre-epoch datetime",
    ),
    AccumulatorTestCase(
        "datetime_epoch_vs_future",
        docs=[{"v": DATE_EPOCH}, {"v": DATE_Y2K}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DATE_EPOCH}],
        msg="$min should pick epoch over Y2K",
    ),
    AccumulatorTestCase(
        "datetime_millisecond_precision",
        docs=[
            {"v": datetime(2020, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc)},
        ],
        pipeline=_group_min("$v"),
        expected=[
            {"_id": None, "result": datetime(2020, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)}
        ],
        msg="$min should distinguish datetimes at millisecond precision",
    ),
    AccumulatorTestCase(
        "datetime_boundaries",
        docs=[{"v": DATE_YEAR_1}, {"v": DATE_YEAR_9999}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DATE_YEAR_1}],
        msg="$min should pick year 1 over year 9999",
    ),
]

# Property [Within-Type Ordering — Timestamp]: lower time wins, then lower increment.
MIN_TIMESTAMP_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "timestamp_lower_time",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(200, 1)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Timestamp(100, 1)}],
        msg="$min should pick timestamp with lower time",
    ),
    AccumulatorTestCase(
        "timestamp_same_time_lower_increment",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(100, 2)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Timestamp(100, 1)}],
        msg="$min should pick timestamp with lower increment when time is equal",
    ),
    AccumulatorTestCase(
        "timestamp_epoch_vs_max",
        docs=[{"v": TS_EPOCH}, {"v": TS_MAX_UNSIGNED32}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": TS_EPOCH}],
        msg="$min should pick epoch timestamp over max",
    ),
    AccumulatorTestCase(
        "timestamp_max_signed32",
        docs=[{"v": Timestamp(2147483647, 1)}, {"v": TS_EPOCH}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": TS_EPOCH}],
        msg="$min should pick epoch over max signed 32-bit timestamp",
    ),
]

# Property [Within-Type Ordering — ObjectId]: earlier timestamp wins, then lower random bytes.
MIN_OBJECTID_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "objectid_earlier_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000000")},
            {"v": ObjectId("000000020000000000000000")},
        ],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": ObjectId("000000010000000000000000")}],
        msg="$min should pick ObjectId with earlier timestamp",
    ),
    AccumulatorTestCase(
        "objectid_same_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000001")},
            {"v": ObjectId("000000010000000000000002")},
        ],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": ObjectId("000000010000000000000001")}],
        msg="$min should pick ObjectId with lower random bytes when timestamp is equal",
    ),
]

# Property [Within-Type Ordering — Binary]: byte-by-byte comparison, lower subtype wins.
MIN_BINARY_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "binary_content",
        docs=[{"v": Binary(b"\x00\x01")}, {"v": Binary(b"\x00\x02")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": b"\x00\x01"}],
        msg="$min should pick binary with lower byte value",
    ),
    AccumulatorTestCase(
        "binary_subtype",
        docs=[{"v": Binary(b"\x00", 0)}, {"v": Binary(b"\x00", 5)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": b"\x00"}],
        msg="$min should pick binary with lower subtype",
    ),
]

# Property [Within-Type Ordering — Regex]: lower pattern string wins.
MIN_REGEX_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "regex_pattern",
        docs=[{"v": Regex("abc")}, {"v": Regex("abd")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Regex("abc")}],
        msg="$min should pick regex with lexicographically smaller pattern",
    ),
    AccumulatorTestCase(
        "regex_flags",
        docs=[{"v": Regex("abc", "i")}, {"v": Regex("abc", "m")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Regex("abc", "i")}],
        msg="$min should compare regex flags when patterns are equal",
    ),
]

# Property [Within-Type Ordering — Code]: lower code string wins.
MIN_CODE_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "code_basic",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Code("a()")}],
        msg="$min should pick Code with lower string value",
    ),
]

# Property [Within-Type Ordering — Object]: recursive field-by-field comparison.
MIN_OBJECT_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "object_first_differing_field",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 3}}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$min should pick object with lesser first differing field value",
    ),
    AccumulatorTestCase(
        "object_more_fields",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1, "b": 2}}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$min should pick object with fewer fields when prefix matches",
    ),
    AccumulatorTestCase(
        "object_empty_vs_nonempty",
        docs=[{"v": {}}, {"v": {"a": 1}}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": {}}],
        msg="$min should pick empty object over non-empty",
    ),
    AccumulatorTestCase(
        "object_nested",
        docs=[{"v": {"a": {"x": 1}}}, {"v": {"a": {"x": 2}}}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": {"a": {"x": 1}}}],
        msg="$min should recursively compare nested objects",
    ),
]

# Property [Within-Type Ordering — Array]: element-by-element comparison.
MIN_ARRAY_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "array_element_by_element",
        docs=[{"v": [1, 2, 3]}, {"v": [1, 2, 4]}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": [1, 2, 3]}],
        msg="$min should compare arrays element by element",
    ),
    AccumulatorTestCase(
        "array_longer_prefix",
        docs=[{"v": [1, 2]}, {"v": [1, 2, 3]}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$min should pick shorter array when it is a prefix",
    ),
    AccumulatorTestCase(
        "array_empty_vs_nonempty",
        docs=[{"v": []}, {"v": [1]}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": []}],
        msg="$min should pick empty array over non-empty",
    ),
    AccumulatorTestCase(
        "array_nested",
        docs=[{"v": [[1]]}, {"v": [[2]]}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": [[1]]}],
        msg="$min should compare nested arrays recursively",
    ),
]

# Property [NaN Handling]: NaN compares as less than all other numeric values.
# For $min, NaN wins over all other numbers.
MIN_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_sole_float",
        docs=[{"v": FLOAT_NAN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should return float NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_sole_decimal",
        docs=[{"v": DECIMAL128_NAN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_NAN}],
        msg="$min should return Decimal128 NaN when it is the sole value",
    ),
    AccumulatorTestCase(
        "nan_decimal_negative",
        docs=[{"v": Decimal128("-NaN")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("-NaN")}],
        msg="$min should preserve -NaN for Decimal128",
    ),
    AccumulatorTestCase(
        "nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 100}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over positive number (NaN < all numerics)",
    ),
    AccumulatorTestCase(
        "nan_vs_negative",
        docs=[{"v": FLOAT_NAN}, {"v": -100}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over negative number",
    ),
    AccumulatorTestCase(
        "nan_vs_neg_infinity",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over -Infinity (NaN < -Infinity)",
    ),
    AccumulatorTestCase(
        "nan_as_only_nonnull",
        docs=[{"v": FLOAT_NAN}, {"v": None}, {"x": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should return NaN when it is the only non-null value",
    ),
    AccumulatorTestCase(
        "nan_three_docs",
        docs=[{"v": FLOAT_NAN}, {"v": 5}, {"v": 10}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over multiple positive values",
    ),
]

# Property [Infinity Handling]: -Infinity < all finite values < +Infinity.
# NaN < -Infinity. For $min, -Infinity wins over finite values.
MIN_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "inf_vs_int32",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT32_MIN}],
        msg="$min should pick INT32_MIN over +Infinity",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_int32",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over INT32_MIN",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_int64",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over INT64_MIN",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_double",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_decimal",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick float -Infinity over DECIMAL128_MIN",
    ),
    AccumulatorTestCase(
        "decimal_neg_inf_vs_double_min",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_NEGATIVE_INFINITY}],
        msg="$min should pick Decimal128 -Infinity over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "inf_vs_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity over +Infinity",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_neg_inf",
        docs=[{"v": Decimal128("Infinity")}, {"v": Decimal128("-Infinity")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("-Infinity")}],
        msg="$min should pick Decimal128 -Infinity over Decimal128 +Infinity",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_string",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": "hello"}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min should pick -Infinity (Number) over String",
    ),
    AccumulatorTestCase(
        "neg_inf_vs_nan",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": FLOAT_NAN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min should pick NaN over -Infinity (NaN < -Infinity)",
    ),
]

# Property [Numeric Boundary Values]: boundary values across all numeric types
# are compared correctly. $min picks the numerically smallest value.
MIN_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max_vs_min",
        docs=[{"v": INT32_MAX}, {"v": INT32_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT32_MIN}],
        msg="$min should pick INT32_MIN over INT32_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_vs_min",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT64_MIN}],
        msg="$min should pick INT64_MIN over INT64_MAX",
    ),
    AccumulatorTestCase(
        "boundary_double_max_vs_min",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_MIN}],
        msg="$min should pick DOUBLE_MIN over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "boundary_decimal_max_vs_min",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MIN}],
        msg="$min should pick DECIMAL128_MIN over DECIMAL128_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_vs_int64_min",
        docs=[{"v": INT32_MIN}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT64_MIN}],
        msg="$min should pick INT64_MIN over INT32_MIN",
    ),
    AccumulatorTestCase(
        "boundary_double_min_vs_int64_min",
        docs=[{"v": DOUBLE_MIN}, {"v": INT64_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_MIN}],
        msg="$min should pick DOUBLE_MIN over INT64_MIN (DOUBLE_MIN is more negative)",
    ),
    AccumulatorTestCase(
        "boundary_decimal_min_vs_double_min",
        docs=[{"v": DECIMAL128_MIN}, {"v": DOUBLE_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MIN}],
        msg="$min should pick DECIMAL128_MIN over DOUBLE_MIN",
    ),
    AccumulatorTestCase(
        "boundary_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": 0.0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 0.0}],
        msg="$min should pick 0.0 over positive subnormal",
    ),
    AccumulatorTestCase(
        "boundary_neg_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, {"v": 0.0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        msg="$min should pick negative subnormal over 0.0",
    ),
    AccumulatorTestCase(
        "boundary_near_max",
        docs=[{"v": DOUBLE_NEAR_MAX}, {"v": DOUBLE_MAX}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DOUBLE_NEAR_MAX}],
        msg="$min should pick DOUBLE_NEAR_MAX over DOUBLE_MAX",
    ),
    AccumulatorTestCase(
        "boundary_int32_adjacent",
        docs=[{"v": INT32_MIN}, {"v": INT32_MIN + 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT32_MIN}],
        msg="$min should pick INT32_MIN over INT32_MIN+1",
    ),
    AccumulatorTestCase(
        "boundary_int64_adjacent",
        docs=[{"v": INT64_MIN}, {"v": Int64(int(INT64_MIN) + 1)}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": INT64_MIN}],
        msg="$min should pick INT64_MIN over INT64_MIN+1",
    ),
]

# Property [Negative Zero]: negative zero and positive zero are numerically equal.
# Tie-breaking by document order differs by stage. These tests use $group (last wins).
MIN_NEGATIVE_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_vs_negative",
        docs=[{"v": -0.0}, {"v": -1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": -1}],
        msg="$min should pick -1 over -0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_vs_negative",
        docs=[{"v": Decimal128("-0")}, {"v": -1.0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": -1.0}],
        msg="$min should pick -1.0 over Decimal128('-0')",
    ),
]

# Property [Decimal128 Precision]: Decimal128 precision boundaries are handled correctly.
MIN_DECIMAL_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_high_precision",
        docs=[
            {"v": Decimal128("1.234567890123456789012345678901234")},
            {"v": Decimal128("1.234567890123456789012345678901235")},
        ],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("1.234567890123456789012345678901234")}],
        msg="$min should compare 34-digit Decimal128 values correctly",
    ),
    AccumulatorTestCase(
        "decimal_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_MAX}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_LARGE_EXPONENT}],
        msg="$min should pick Decimal128 with smaller large exponent",
    ),
    AccumulatorTestCase(
        "decimal_min_positive",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_ZERO}],
        msg="$min should pick zero over min positive Decimal128",
    ),
    AccumulatorTestCase(
        "decimal_max_negative",
        docs=[{"v": DECIMAL128_MAX_NEGATIVE}, {"v": DECIMAL128_ZERO}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MAX_NEGATIVE}],
        msg="$min should pick max negative Decimal128 over zero",
    ),
    AccumulatorTestCase(
        "decimal_inf_vs_max",
        docs=[{"v": Decimal128("Infinity")}, {"v": DECIMAL128_MAX}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_MAX}],
        msg="$min should pick DECIMAL128_MAX over Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "decimal_neg_inf_vs_min",
        docs=[{"v": Decimal128("-Infinity")}, {"v": DECIMAL128_MIN}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("-Infinity")}],
        msg="$min should pick Decimal128 -Infinity over DECIMAL128_MIN",
    ),
    AccumulatorTestCase(
        "decimal_nan_vs_finite",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": DECIMAL128_NAN}],
        msg="$min should pick Decimal128 NaN over finite Decimal128 (NaN < all)",
    ),
]

# Property [BSON Type Distinction]: values of different BSON types are distinct
# even when they appear similar. For $min, the lower BSON type wins.
MIN_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 0}],
        msg="$min should pick Number(0) over Boolean(false) (Number < Boolean)",
    ),
    AccumulatorTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 1}],
        msg="$min should pick Number(1) over Boolean(true) (Number < Boolean)",
    ),
    AccumulatorTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": ""}],
        msg="$min should exclude null and return empty string",
    ),
    AccumulatorTestCase(
        "distinct_numeric_string",
        docs=[{"v": "123"}, {"v": 1_000_000}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 1_000_000}],
        msg="$min should pick Number over numeric-looking String (Number < String)",
    ),
]

# Property [Expression Argument Tests]: $min accumulator accepts various
# expression types as its operand.
MIN_EXPRESSION_ARGUMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "input_field_path",
        docs=[{"v": 10}, {"v": 5}, {"v": 20}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should accept basic field reference",
    ),
    AccumulatorTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 5}}, {"a": {"b": 20}}],
        pipeline=_group_min("$a.b"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should accept nested document field path",
    ),
    AccumulatorTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}, {"v": 3}],
        pipeline=_group_min(42),
        expected=[{"_id": None, "result": 42}],
        msg="$min should accept constant literal (same for all docs)",
    ),
    AccumulatorTestCase(
        "input_expression",
        docs=[{"price": 10, "qty": 2}, {"price": 5, "qty": 3}, {"price": 20, "qty": 1}],
        pipeline=_group_min({"$multiply": ["$price", "$qty"]}),
        expected=[{"_id": None, "result": 15}],
        msg="$min should accept computed expression as operand",
    ),
    AccumulatorTestCase(
        "input_cond_remove",
        docs=[{"v": -1}, {"v": 5}, {"v": -2}, {"v": 10}],
        pipeline=_group_min({"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}),
        expected=[{"_id": None, "result": 5}],
        msg="$min should accept conditional expression with $$REMOVE",
    ),
    AccumulatorTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=_group_min(None),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when accumulator is null literal",
    ),
]

# Property [Return Type Verification]: $min preserves the BSON type of the minimum value.
MIN_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_int32",
        docs=[{"v": 10}, {"v": 20}, {"v": 30}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 10, "type": "int"}],
        msg="$min should preserve int32 return type",
    ),
    AccumulatorTestCase(
        "return_type_int64",
        docs=[{"v": Int64(10)}, {"v": Int64(20)}, {"v": Int64(30)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Int64(10), "type": "long"}],
        msg="$min should preserve int64 return type",
    ),
    AccumulatorTestCase(
        "return_type_double",
        docs=[{"v": 1.5}, {"v": 2.5}, {"v": 3.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 1.5, "type": "double"}],
        msg="$min should preserve double return type",
    ),
    AccumulatorTestCase(
        "return_type_decimal",
        docs=[{"v": Decimal128("1.5")}, {"v": Decimal128("2.5")}, {"v": Decimal128("3.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Decimal128("1.5"), "type": "decimal"}],
        msg="$min should preserve Decimal128 return type",
    ),
    AccumulatorTestCase(
        "return_type_string",
        docs=[{"v": "apple"}, {"v": "banana"}, {"v": "cherry"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": "apple", "type": "string"}],
        msg="$min should preserve string return type",
    ),
    AccumulatorTestCase(
        "return_type_boolean",
        docs=[{"v": True}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": False, "type": "bool"}],
        msg="$min should preserve boolean return type",
    ),
    AccumulatorTestCase(
        "return_type_date",
        docs=[{"v": DATE_EPOCH}, {"v": DATE_Y2K}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": DATE_EPOCH, "type": "date"}],
        msg="$min should preserve date return type",
    ),
    AccumulatorTestCase(
        "return_type_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": None, "type": "null"}],
        msg="$min should return null type when all values are null",
    ),
]

# Property [Accumulator Edge Cases]: edge cases unique to accumulator context.
MIN_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 42}],
        msg="$min should return value when only one document in group",
    ),
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null for single null document",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": None}],
        msg="$min should return null for single document with missing field",
    ),
    AccumulatorTestCase(
        "edge_multi_group",
        docs=[
            {"g": "A", "v": 10},
            {"g": "A", "v": 5},
            {"g": "B", "v": 20},
            {"g": "B", "v": 15},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$min": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "result": 5}, {"_id": "B", "result": 15}],
        msg="$min should compute independently per group",
    ),
    AccumulatorTestCase(
        "edge_many_docs",
        docs=[{"v": i} for i in range(100, 0, -1)],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 1}],
        msg="$min should correctly compute over 100+ documents",
    ),
    AccumulatorTestCase(
        "edge_array_field_not_traversed",
        docs=[{"v": [5, 1, 8]}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": [5, 1, 8]}],
        msg="$min should treat array field as a whole value, not traverse elements",
    ),
    AccumulatorTestCase(
        "edge_mixed_array_scalar",
        docs=[{"v": [1, 2, 3]}, {"v": 5}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 5}],
        msg="$min should pick scalar Number over Array (Number < Array in BSON)",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate for $group success tests (categories 1–16)
# ---------------------------------------------------------------------------
MIN_GROUP_SUCCESS_TESTS = (
    MIN_NULL_MISSING_TESTS
    + MIN_BSON_ORDER_TESTS
    + MIN_NUMERIC_ORDERING_TESTS
    + MIN_STRING_ORDERING_TESTS
    + MIN_BOOLEAN_ORDERING_TESTS
    + MIN_DATETIME_ORDERING_TESTS
    + MIN_TIMESTAMP_ORDERING_TESTS
    + MIN_OBJECTID_ORDERING_TESTS
    + MIN_BINARY_ORDERING_TESTS
    + MIN_REGEX_ORDERING_TESTS
    + MIN_CODE_ORDERING_TESTS
    + MIN_OBJECT_ORDERING_TESTS
    + MIN_ARRAY_ORDERING_TESTS
    + MIN_NAN_TESTS
    + MIN_INFINITY_TESTS
    + MIN_BOUNDARY_TESTS
    + MIN_NEGATIVE_ZERO_TESTS
    + MIN_DECIMAL_PRECISION_TESTS
    + MIN_TYPE_DISTINCTION_TESTS
    + MIN_EXPRESSION_ARGUMENT_TESTS
    + MIN_EDGE_CASE_TESTS
)

# ---------------------------------------------------------------------------
# Error tests — categories 12, 14 ($group)
# ---------------------------------------------------------------------------

# Property [Expression Error Propagation]: errors in sub-expressions used as
# $min operand propagate as errors.
MIN_EXPRESSION_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid",
        docs=[{"v": "not_a_number"}],
        pipeline=_group_min({"$toInt": "$v"}),
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$min should propagate $toInt conversion error",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=_group_min({"$divide": ["$v", 0]}),
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$min should propagate divide-by-zero error",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=_group_min({"$mod": ["$v", 0]}),
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$min should propagate mod-by-zero error",
    ),
]

# Property [Arity Rejection]: $min in accumulator context is unary and rejects
# array syntax.
MIN_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=_group_min([]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element",
        docs=[{"v": 1}],
        pipeline=_group_min([1]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref",
        docs=[{"v": 1}],
        pipeline=_group_min(["$v"]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element",
        docs=[{"v": 1}],
        pipeline=_group_min([1, 2, 3]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression",
        docs=[{"v": 1}],
        pipeline=_group_min({"$add": [1, 2], "$multiply": [3, 4]}),
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$min should reject multi-key expression object",
    ),
]

MIN_GROUP_ERROR_TESTS = MIN_EXPRESSION_ERROR_GROUP_TESTS + MIN_ARITY_ERROR_TESTS

# ---------------------------------------------------------------------------
# $bucket smoke tests (category 17)
# ---------------------------------------------------------------------------

# Property [$bucket Smoke]: representative subset confirming $min works in $bucket context.
MIN_BUCKET_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=_bucket_min("$v"),
        expected=[{"_id": -1, "result": 10}],
        msg="$min in $bucket should return smallest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_null_among_values",
        docs=[{"v": None}, {"v": 10}, {"v": 5}],
        pipeline=_bucket_min("$v"),
        expected=[{"_id": -1, "result": 5}],
        msg="$min in $bucket should exclude null and return min of numerics",
    ),
    AccumulatorTestCase(
        "bucket_bson_cross_type",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=_bucket_min("$v"),
        expected=[{"_id": -1, "result": 100}],
        msg="$min in $bucket should pick Number over String (Number < String)",
    ),
    AccumulatorTestCase(
        "bucket_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 100}],
        pipeline=_bucket_min("$v"),
        expected=[{"_id": -1, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min in $bucket should pick NaN over positive number",
    ),
    AccumulatorTestCase(
        "bucket_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=_bucket_min("$v"),
        expected=[{"_id": -1, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min in $bucket should pick -Infinity over INT32_MIN",
    ),
]

# Property [$bucket Smoke — Errors]: arity and expression errors in $bucket.
MIN_BUCKET_SMOKE_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_arity_rejection",
        docs=[{"v": 1}],
        pipeline=_bucket_min([]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min in $bucket should reject array syntax",
    ),
    AccumulatorTestCase(
        "bucket_expression_error",
        docs=[{"v": 10}],
        pipeline=_bucket_min({"$divide": ["$v", 0]}),
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$min in $bucket should propagate divide-by-zero error",
    ),
]

# ---------------------------------------------------------------------------
# $bucketAuto smoke tests (category 17)
# ---------------------------------------------------------------------------

# Property [$bucketAuto Smoke]: representative subset confirming $min works in $bucketAuto context.
MIN_BUCKET_AUTO_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": 10}],
        msg="$min in $bucketAuto should return smallest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_auto_null_among_values",
        docs=[{"v": None}, {"v": 10}, {"v": 5}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": 5}],
        msg="$min in $bucketAuto should exclude null and return min of numerics",
    ),
    AccumulatorTestCase(
        "bucket_auto_bson_cross_type",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": 100}],
        msg="$min in $bucketAuto should pick Number over String",
    ),
    AccumulatorTestCase(
        "bucket_auto_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 100}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min in $bucketAuto should pick NaN over positive number",
    ),
    AccumulatorTestCase(
        "bucket_auto_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min in $bucketAuto should pick -Infinity over INT32_MIN",
    ),
]

# Property [$bucketAuto Smoke — Errors]: arity and expression errors in $bucketAuto.
MIN_BUCKET_AUTO_SMOKE_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_arity_rejection",
        docs=[{"v": 1}],
        pipeline=_bucket_auto_min([]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min in $bucketAuto should reject array syntax",
    ),
    AccumulatorTestCase(
        "bucket_auto_expression_error",
        docs=[{"v": 10}],
        pipeline=_bucket_auto_min({"$divide": ["$v", 0]}),
        error_code=BAD_VALUE_ERROR,
        msg="$min in $bucketAuto should wrap divide-by-zero as BAD_VALUE_ERROR",
    ),
]

# ---------------------------------------------------------------------------
# Stage-specific behavior tests (category 17 — where stages diverge)
# ---------------------------------------------------------------------------

# Property [Tie-Breaking — $group]: when numerically equal values have different
# types, $group preserves the last encountered type.
MIN_TIE_BREAKING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_group",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "long", "value": Int64(5)}],
        msg="$min in $group should preserve last type (int64) for equal int32 and int64",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_group",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $group should preserve last type (int32) for equal int64 and int32",
    ),
    AccumulatorTestCase(
        "tie_double_int32_group",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $group should preserve last type (int32) for equal double and int32",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_group",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "long", "value": Int64(5)}],
        msg="$min in $group should preserve last type (int64) for equal Decimal128 and int64",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_group",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("5")}],
        msg="$min in $group should preserve last type (Decimal128) for all four equal types",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_group",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $group should preserve last type (int32) in reversed order",
    ),
]

# Property [Tie-Breaking — $bucketAuto]: when numerically equal values have different
# types, $bucketAuto preserves the first encountered type.
MIN_TIE_BREAKING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $bucketAuto should preserve first type (int32) for equal int32 and int64",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_bucket_auto",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "long", "value": Int64(5)}],
        msg="$min in $bucketAuto should preserve first type (int64) for equal int64 and int32",
    ),
    AccumulatorTestCase(
        "tie_double_int32_bucket_auto",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "double", "value": 5.0}],
        msg="$min in $bucketAuto should preserve first type (double) for equal double and int32",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("5")}],
        msg="$min in $bucketAuto should preserve first type (Decimal128) for equal values",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $bucketAuto should preserve first type (int32) for all four equal types",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("5")}],
        msg="$min in $bucketAuto should preserve first type (Decimal128) in reversed order",
    ),
]

# Property [Numeric Equivalence — $group]: numerically equivalent values across
# types are treated as equal. $group: last type wins.
MIN_NUMERIC_EQUIV_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_int_long_double_decimal_group",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("5")}],
        msg="$min in $group should pick last type (Decimal128) for equal values",
    ),
    AccumulatorTestCase(
        "equiv_zeros_group",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": 0.0}, {"v": Decimal128("0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("0")}],
        msg="$min in $group should pick last type (Decimal128) for equivalent zeros",
    ),
]

# Property [Numeric Equivalence — $bucketAuto]: $bucketAuto: first type wins.
MIN_NUMERIC_EQUIV_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_int_long_double_decimal_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $bucketAuto should pick first type (int32) for equal values",
    ),
    AccumulatorTestCase(
        "equiv_zeros_bucket_auto",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": 0.0}, {"v": Decimal128("0")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 0}],
        msg="$min in $bucketAuto should pick first type (int32) for equivalent zeros",
    ),
]

# Property [Negative Zero Tie-Breaking — $group]: $group last-wins for -0.0 vs 0.0.
MIN_NEGZERO_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_group",
        docs=[{"v": -0.0}, {"v": 0.0}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": 0.0}],
        msg="$min in $group should return 0.0 (last wins) for -0.0 vs 0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_group",
        docs=[{"v": Decimal128("-0")}, {"v": Decimal128("0")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("0")}],
        msg="$min in $group should return Decimal128('0') (last wins) for Decimal128 -0 vs 0",
    ),
]

# Property [Negative Zero Tie-Breaking — $bucketAuto]: $bucketAuto first-wins.
MIN_NEGZERO_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_bucket_auto",
        docs=[{"v": -0.0}, {"v": 0.0}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": -0.0}],
        msg="$min in $bucketAuto should return -0.0 (first wins) for -0.0 vs 0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_bucket_auto",
        docs=[{"v": Decimal128("-0")}, {"v": Decimal128("0")}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": Decimal128("-0")}],
        msg="$min in $bucketAuto should return Decimal128('-0') (first wins)",
    ),
]

# Property [NaN Type Tie-Breaking — $group]: float NaN and Decimal128 NaN tie-break.
MIN_NAN_TIE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_group",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$min in $group should preserve Decimal128 NaN type (last wins)",
    ),
]

# Property [NaN Type Tie-Breaking — $bucketAuto]: first-wins.
MIN_NAN_TIE_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_bucket_auto",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$min in $bucketAuto should preserve float NaN type (first wins)",
    ),
]

# Property [Decimal Trailing Zeros — $group]: Decimal128("1.0") vs Decimal128("1.00").
MIN_DECIMAL_TRAILING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_group",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Decimal128("1.00")}],
        msg="$min in $group should return Decimal128('1.00') (last wins) for trailing zero tie",
    ),
]

# Property [Decimal Trailing Zeros — $bucketAuto]: first-wins.
MIN_DECIMAL_TRAILING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_bucket_auto",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": Decimal128("1.0")}],
        msg="$min in $bucketAuto should return Decimal128('1.0') for trailing zero tie",
    ),
]

# Property [BSON Serialization — $group]: Code returned as Code object,
# MinKey returned directly in $group.
MIN_BSON_SERIALIZATION_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_group",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Regex("zzz")}],
        msg="$min in $group should return Regex as Regex object (Regex < Code)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_group",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Code("zzz")}],
        msg="$min in $group should return Code as Code object",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_group",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": MinKey()}],
        msg="$min in $group should return MinKey directly",
    ),
    AccumulatorTestCase(
        "bson_code_basic_group",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=_group_min("$v"),
        expected=[{"_id": None, "result": Code("a()")}],
        msg="$min in $group should return Code as Code object",
    ),
]

# Property [BSON Serialization — $bucketAuto]: Code without scope returned as Code object,
# MinKey returned directly.
MIN_BSON_SERIALIZATION_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_bucket_auto",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": Regex("zzz")}],
        msg="$min in $bucketAuto should return Regex as Regex object (Regex < Code)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_bucket_auto",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": Code("zzz")}],
        msg="$min in $bucketAuto should return Code as Code object",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_bucket_auto",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": MinKey()}],
        msg="$min in $bucketAuto should return MinKey directly",
    ),
    AccumulatorTestCase(
        "bson_code_basic_bucket_auto",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=_bucket_auto_min("$v"),
        expected=[{"_id": {"min": 0, "max": 0}, "result": Code("a()")}],
        msg="$min in $bucketAuto should return Code as Code object",
    ),
]

# Property [Expression Error Codes — $bucketAuto]: $bucketAuto wraps some errors
# with different codes.
MIN_EXPRESSION_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_divide_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=_bucket_auto_min({"$divide": ["$v", 0]}),
        error_code=BAD_VALUE_ERROR,
        msg="$min in $bucketAuto should wrap divide-by-zero as BAD_VALUE_ERROR",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=_bucket_auto_min({"$mod": ["$v", 0]}),
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="$min in $bucketAuto should wrap mod-by-zero as MODULO_ZERO_REMAINDER_ERROR",
    ),
]


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------


def _run_accumulator(collection, test_case: AccumulatorTestCase):
    """Insert docs and run the pipeline."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_SUCCESS_TESTS))
def test_accumulator_min_group(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator success cases with $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_ERROR_TESTS))
def test_accumulator_min_group_errors(collection, test_case):
    """Test $min accumulator error cases with $group."""
    result = _run_accumulator(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_RETURN_TYPE_TESTS))
def test_accumulator_min_return_type(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator return type verification."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_BUCKET_SMOKE_TESTS))
def test_accumulator_min_bucket_smoke(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator in $bucket context."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_BUCKET_SMOKE_ERROR_TESTS))
def test_accumulator_min_bucket_smoke_errors(collection, test_case):
    """Test $min accumulator errors in $bucket context."""
    result = _run_accumulator(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_BUCKET_AUTO_SMOKE_TESTS))
def test_accumulator_min_bucket_auto_smoke(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator in $bucketAuto context."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_BUCKET_AUTO_SMOKE_ERROR_TESTS))
def test_accumulator_min_bucket_auto_smoke_errors(collection, test_case):
    """Test $min accumulator errors in $bucketAuto context."""
    result = _run_accumulator(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_TIE_BREAKING_GROUP_TESTS))
def test_accumulator_min_tie_breaking_group(collection, test_case: AccumulatorTestCase):
    """Test $min tie-breaking in $group (last type wins)."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_TIE_BREAKING_BUCKET_AUTO_TESTS))
def test_accumulator_min_tie_breaking_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $min tie-breaking in $bucketAuto (first type wins)."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NUMERIC_EQUIV_GROUP_TESTS))
def test_accumulator_min_numeric_equiv_group(collection, test_case: AccumulatorTestCase):
    """Test $min numeric equivalence in $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NUMERIC_EQUIV_BUCKET_AUTO_TESTS))
def test_accumulator_min_numeric_equiv_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $min numeric equivalence in $bucketAuto."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NEGZERO_GROUP_TESTS))
def test_accumulator_min_negzero_group(collection, test_case: AccumulatorTestCase):
    """Test $min negative zero tie-breaking in $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NEGZERO_BUCKET_AUTO_TESTS))
def test_accumulator_min_negzero_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $min negative zero tie-breaking in $bucketAuto."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NAN_TIE_GROUP_TESTS))
def test_accumulator_min_nan_tie_group(collection, test_case: AccumulatorTestCase):
    """Test $min NaN type tie-breaking in $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_NAN_TIE_BUCKET_AUTO_TESTS))
def test_accumulator_min_nan_tie_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $min NaN type tie-breaking in $bucketAuto."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_DECIMAL_TRAILING_GROUP_TESTS))
def test_accumulator_min_decimal_trailing_group(collection, test_case: AccumulatorTestCase):
    """Test $min Decimal128 trailing zeros tie-breaking in $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_DECIMAL_TRAILING_BUCKET_AUTO_TESTS))
def test_accumulator_min_decimal_trailing_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $min Decimal128 trailing zeros tie-breaking in $bucketAuto."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_BSON_SERIALIZATION_GROUP_TESTS))
def test_accumulator_min_bson_serialization_group(collection, test_case: AccumulatorTestCase):
    """Test $min BSON serialization in $group."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_BSON_SERIALIZATION_BUCKET_AUTO_TESTS))
def test_accumulator_min_bson_serialization_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $min BSON serialization in $bucketAuto."""
    result = _run_accumulator(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_EXPRESSION_ERROR_BUCKET_AUTO_TESTS))
def test_accumulator_min_expression_errors_bucket_auto(collection, test_case):
    """Test $min expression error codes in $bucketAuto."""
    result = _run_accumulator(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
