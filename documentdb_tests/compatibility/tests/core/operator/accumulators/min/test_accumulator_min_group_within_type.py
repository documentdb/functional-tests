"""Tests for $min accumulator — within-type ordering ($group)."""

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
    TS_MAX_UNSIGNED32,
)

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Numeric]: values of the same numeric type
# follow standard numeric ordering. $min picks the smallest value.
# ---------------------------------------------------------------------------
MIN_NUMERIC_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "numeric_int32_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 10}],
        msg="$min should return smallest int32 value",
    ),
    AccumulatorTestCase(
        "numeric_int64_basic",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Int64(100)}],
        msg="$min should return smallest int64 value",
    ),
    AccumulatorTestCase(
        "numeric_double_basic",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 1.5}],
        msg="$min should return smallest double value",
    ),
    AccumulatorTestCase(
        "numeric_decimal128_basic",
        docs=[{"v": Decimal128("1.5")}, {"v": Decimal128("3.5")}, {"v": Decimal128("2.5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("1.5")}],
        msg="$min should return smallest Decimal128 value",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_int64",
        docs=[{"v": 10}, {"v": Int64(5)}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Int64(5)}],
        msg="$min should compare int32 and int64 numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_double",
        docs=[{"v": 10}, {"v": 5.5}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 5.5}],
        msg="$min should compare int32 and double numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int32_decimal",
        docs=[{"v": 10}, {"v": Decimal128("5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("5")}],
        msg="$min should compare int32 and Decimal128 numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_double",
        docs=[{"v": Int64(10)}, {"v": 5.5}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 5.5}],
        msg="$min should compare int64 and double numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_int64_decimal",
        docs=[{"v": Int64(10)}, {"v": Decimal128("5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("5")}],
        msg="$min should compare int64 and Decimal128 numerically",
    ),
    AccumulatorTestCase(
        "numeric_cross_double_decimal",
        docs=[{"v": 10.5}, {"v": Decimal128("5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("5")}],
        msg="$min should compare double and Decimal128 numerically",
    ),
    AccumulatorTestCase(
        "numeric_all_four_types",
        docs=[{"v": 4}, {"v": Int64(3)}, {"v": 2.0}, {"v": Decimal128("1")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("1")}],
        msg="$min should pick smallest across all four numeric types",
    ),
    AccumulatorTestCase(
        "numeric_ieee754_rounding",
        docs=[{"v": 3.14}, {"v": Decimal128("3.14")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("3.14")}],
        msg="$min should pick Decimal128('3.14') over double 3.14 due to IEEE 754 rounding",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — String]: strings are compared by byte value.
# ---------------------------------------------------------------------------
MIN_STRING_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "abc"}],
        msg="$min should pick lexicographically smaller string",
    ),
    AccumulatorTestCase(
        "string_case",
        docs=[{"v": "a"}, {"v": "A"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "A"}],
        msg="$min should pick uppercase over lowercase (byte value comparison)",
    ),
    AccumulatorTestCase(
        "string_unicode_no_normalization",
        docs=[{"v": "\u00e9"}, {"v": "\u0065\u0301"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "\u0065\u0301"}],
        msg="$min should distinguish precomposed and decomposed Unicode (no normalization)",
    ),
    AccumulatorTestCase(
        "string_digits_lexicographic",
        docs=[{"v": "9"}, {"v": "10"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "10"}],
        msg="$min should compare digit strings lexicographically ('1' < '9')",
    ),
    AccumulatorTestCase(
        "string_null_byte",
        docs=[{"v": "a\x00b"}, {"v": "a\x00c"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "a\x00b"}],
        msg="$min should compare strings with embedded null bytes by byte value",
    ),
    AccumulatorTestCase(
        "string_prefix",
        docs=[{"v": "abc"}, {"v": "abcd"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "abc"}],
        msg="$min should pick shorter string when it is a prefix of the longer",
    ),
    AccumulatorTestCase(
        "string_empty_vs_nonempty",
        docs=[{"v": ""}, {"v": "a"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": ""}],
        msg="$min should pick empty string over non-empty",
    ),
    AccumulatorTestCase(
        "string_4byte_utf8",
        docs=[{"v": "\U0001f600"}, {"v": "\U0001f601"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "\U0001f600"}],
        msg="$min should compare 4-byte UTF-8 characters by byte value",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Boolean]: False < True.
# ---------------------------------------------------------------------------
MIN_BOOLEAN_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boolean_true_vs_false",
        docs=[{"v": True}, {"v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": False}],
        msg="$min should pick False over True",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Datetime]: earlier datetimes are smaller.
# ---------------------------------------------------------------------------
MIN_DATETIME_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "datetime_chronological",
        docs=[
            {"v": datetime(2020, 6, 15, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$min should pick earlier datetime",
    ),
    AccumulatorTestCase(
        "datetime_pre_epoch_vs_epoch",
        docs=[{"v": DATE_BEFORE_EPOCH}, {"v": DATE_EPOCH}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": DATE_BEFORE_EPOCH}],
        msg="$min should pick pre-epoch datetime",
    ),
    AccumulatorTestCase(
        "datetime_epoch_vs_future",
        docs=[{"v": DATE_EPOCH}, {"v": DATE_Y2K}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": DATE_EPOCH}],
        msg="$min should pick epoch over Y2K",
    ),
    AccumulatorTestCase(
        "datetime_millisecond_precision",
        docs=[
            {"v": datetime(2020, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[
            {"_id": None, "result": datetime(2020, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)}
        ],
        msg="$min should distinguish datetimes at millisecond precision",
    ),
    AccumulatorTestCase(
        "datetime_boundaries",
        docs=[{"v": DATE_YEAR_1}, {"v": DATE_YEAR_9999}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": DATE_YEAR_1}],
        msg="$min should pick year 1 over year 9999",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Timestamp]: lower time wins, then lower increment.
# ---------------------------------------------------------------------------
MIN_TIMESTAMP_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "timestamp_lower_time",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(200, 1)}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Timestamp(100, 1)}],
        msg="$min should pick timestamp with lower time",
    ),
    AccumulatorTestCase(
        "timestamp_same_time_lower_increment",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(100, 2)}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Timestamp(100, 1)}],
        msg="$min should pick timestamp with lower increment when time is equal",
    ),
    AccumulatorTestCase(
        "timestamp_epoch_vs_max",
        docs=[{"v": TS_EPOCH}, {"v": TS_MAX_UNSIGNED32}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": TS_EPOCH}],
        msg="$min should pick epoch timestamp over max",
    ),
    AccumulatorTestCase(
        "timestamp_max_signed32",
        docs=[{"v": Timestamp(2147483647, 1)}, {"v": TS_EPOCH}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": TS_EPOCH}],
        msg="$min should pick epoch over max signed 32-bit timestamp",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — ObjectId]: earlier timestamp wins, then lower random bytes.
# ---------------------------------------------------------------------------
MIN_OBJECTID_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "objectid_earlier_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000000")},
            {"v": ObjectId("000000020000000000000000")},
        ],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": ObjectId("000000010000000000000000")}],
        msg="$min should pick ObjectId with earlier timestamp",
    ),
    AccumulatorTestCase(
        "objectid_same_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000001")},
            {"v": ObjectId("000000010000000000000002")},
        ],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": ObjectId("000000010000000000000001")}],
        msg="$min should pick ObjectId with lower random bytes when timestamp is equal",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Binary]: byte-by-byte comparison, lower subtype wins.
# ---------------------------------------------------------------------------
MIN_BINARY_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "binary_content",
        docs=[{"v": Binary(b"\x00\x01")}, {"v": Binary(b"\x00\x02")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": b"\x00\x01"}],
        msg="$min should pick binary with lower byte value",
    ),
    AccumulatorTestCase(
        "binary_subtype",
        docs=[{"v": Binary(b"\x00", 0)}, {"v": Binary(b"\x00", 5)}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": b"\x00"}],
        msg="$min should pick binary with lower subtype",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Regex]: lower pattern string wins.
# ---------------------------------------------------------------------------
MIN_REGEX_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "regex_pattern",
        docs=[{"v": Regex("abc")}, {"v": Regex("abd")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Regex("abc")}],
        msg="$min should pick regex with lexicographically smaller pattern",
    ),
    AccumulatorTestCase(
        "regex_flags",
        docs=[{"v": Regex("abc", "i")}, {"v": Regex("abc", "m")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Regex("abc", "i")}],
        msg="$min should compare regex flags when patterns are equal",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Object]: recursive field-by-field comparison.
# ---------------------------------------------------------------------------
MIN_OBJECT_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "object_first_differing_field",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 3}}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$min should pick object with lesser first differing field value",
    ),
    AccumulatorTestCase(
        "object_more_fields",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1, "b": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$min should pick object with fewer fields when prefix matches",
    ),
    AccumulatorTestCase(
        "object_empty_vs_nonempty",
        docs=[{"v": {}}, {"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": {}}],
        msg="$min should pick empty object over non-empty",
    ),
    AccumulatorTestCase(
        "object_nested",
        docs=[{"v": {"a": {"x": 1}}}, {"v": {"a": {"x": 2}}}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": {"a": {"x": 1}}}],
        msg="$min should recursively compare nested objects",
    ),
]

# ---------------------------------------------------------------------------
# Property [Within-Type Ordering — Array]: element-by-element comparison.
# ---------------------------------------------------------------------------
MIN_ARRAY_ORDERING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "array_element_by_element",
        docs=[{"v": [1, 2, 3]}, {"v": [1, 2, 4]}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": [1, 2, 3]}],
        msg="$min should compare arrays element by element",
    ),
    AccumulatorTestCase(
        "array_longer_prefix",
        docs=[{"v": [1, 2]}, {"v": [1, 2, 3]}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$min should pick shorter array when it is a prefix",
    ),
    AccumulatorTestCase(
        "array_empty_vs_nonempty",
        docs=[{"v": []}, {"v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$min should pick empty array over non-empty",
    ),
    AccumulatorTestCase(
        "array_nested",
        docs=[{"v": [[1]]}, {"v": [[2]]}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": [[1]]}],
        msg="$min should compare nested arrays recursively",
    ),
]


# ---------------------------------------------------------------------------
# Combined success tests
# ---------------------------------------------------------------------------
MIN_GROUP_WITHIN_TYPE_SUCCESS_TESTS = (
    MIN_NUMERIC_ORDERING_TESTS
    + MIN_STRING_ORDERING_TESTS
    + MIN_BOOLEAN_ORDERING_TESTS
    + MIN_DATETIME_ORDERING_TESTS
    + MIN_TIMESTAMP_ORDERING_TESTS
    + MIN_OBJECTID_ORDERING_TESTS
    + MIN_BINARY_ORDERING_TESTS
    + MIN_REGEX_ORDERING_TESTS
    + MIN_OBJECT_ORDERING_TESTS
    + MIN_ARRAY_ORDERING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_WITHIN_TYPE_SUCCESS_TESTS))
def test_accumulator_min_group_within_type(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator within-type ordering with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
