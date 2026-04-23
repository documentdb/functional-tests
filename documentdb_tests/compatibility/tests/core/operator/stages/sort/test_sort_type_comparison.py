from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Type Comparison Order]: documents with values of different
# BSON types sort according to the BSON comparison order.
SORT_BSON_TYPE_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "bson_order_all_types_asc",
        docs=[
            {"_id": 1, "v": MaxKey()},
            {"_id": 2, "v": Code("f", {"x": 1})},
            {"_id": 3, "v": Code("f")},
            {"_id": 4, "v": Regex("a")},
            {"_id": 5, "v": Timestamp(1, 1)},
            {"_id": 6, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 7, "v": True},
            {"_id": 8, "v": ObjectId("000000000000000000000001")},
            {"_id": 9, "v": Binary(b"\x01")},
            {"_id": 10, "v": {"a": 1}},
            {"_id": 11, "v": "hello"},
            {"_id": 12, "v": 42},
            {"_id": 13, "v": None},
            {"_id": 14},
            {"_id": 15, "v": MinKey()},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 15, "v": MinKey()},
            {"_id": 13, "v": None},
            {"_id": 14},
            {"_id": 12, "v": 42},
            {"_id": 11, "v": "hello"},
            {"_id": 10, "v": {"a": 1}},
            {"_id": 9, "v": b"\x01"},
            {"_id": 8, "v": ObjectId("000000000000000000000001")},
            {"_id": 7, "v": True},
            {"_id": 6, "v": datetime(2024, 1, 1)},
            {"_id": 5, "v": Timestamp(1, 1)},
            {"_id": 4, "v": Regex("a")},
            {"_id": 3, "v": Code("f")},
            {"_id": 2, "v": Code("f", {"x": 1})},
            {"_id": 1, "v": MaxKey()},
        ],
        msg="$sort should order BSON types according to the BSON comparison order",
    ),
]

# Property [Within-Type Ordering]: values of the same BSON type sort by
# their type-specific comparison rules rather than by BSON subtype grouping.
SORT_WITHIN_TYPE_TESTS: list[StageTestCase] = [
    # Strings sort in binary/codepoint order with no Unicode normalization,
    # no null-byte truncation, and no special handling of invisible characters.
    StageTestCase(
        "within_string_codepoint_order",
        docs=[
            {"_id": 5, "v": "\u00e9"},
            {"_id": 4, "v": "e\u0301"},
            {"_id": 3, "v": "ab\x00c"},
            {"_id": 2, "v": "abc"},
            {"_id": 1, "v": "\u200b"},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 3, "v": "ab\x00c"},
            {"_id": 2, "v": "abc"},
            {"_id": 4, "v": "e\u0301"},
            {"_id": 5, "v": "\u00e9"},
            {"_id": 1, "v": "\u200b"},
        ],
        msg="$sort should sort strings by binary codepoint order without normalization",
    ),
    StageTestCase(
        "within_string_digit_strings_as_strings",
        docs=[
            {"_id": 1, "v": "0"},
            {"_id": 2, "v": 99_999},
            {"_id": 3, "v": "12345"},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 2, "v": 99_999},
            {"_id": 1, "v": "0"},
            {"_id": 3, "v": "12345"},
        ],
        msg="$sort should sort digit-only strings as strings after numbers",
    ),
    StageTestCase(
        "within_objectid_byte_comparison",
        docs=[
            {"_id": 1, "v": ObjectId("ffffffffffffffffffff0001")},
            {"_id": 2, "v": ObjectId("000000000000000000000001")},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": ObjectId("000000000000000000000001")},
            {"_id": 1, "v": ObjectId("ffffffffffffffffffff0001")},
        ],
        msg="$sort should sort ObjectId values by lexicographic byte comparison",
    ),
    StageTestCase(
        "within_regex_pattern_then_flags",
        docs=[
            {"_id": 1, "v": Regex("abc", "i")},
            {"_id": 2, "v": Regex("abc", "")},
            {"_id": 3, "v": Regex("abd", "")},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": Regex("abc", "")},
            {"_id": 1, "v": Regex("abc", "i")},
            {"_id": 3, "v": Regex("abd", "")},
        ],
        msg="$sort should sort Regex by pattern first then by flags",
    ),
    StageTestCase(
        "within_embedded_doc_order",
        docs=[
            {"_id": 1, "v": {"a": 2}},
            {"_id": 2, "v": {}},
            {"_id": 3, "v": {"b": 1}},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": {}},
            {"_id": 1, "v": {"a": 2}},
            {"_id": 3, "v": {"b": 1}},
        ],
        msg=(
            "$sort should sort embedded documents by key-value pairs in order"
            " with empty document first"
        ),
    ),
    StageTestCase(
        "within_code_lexicographic",
        docs=[
            {"_id": 1, "v": Code("function b() {}")},
            {"_id": 2, "v": Code("function a() {}")},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": Code("function a() {}")},
            {"_id": 1, "v": Code("function b() {}")},
        ],
        msg="$sort should sort Code values by code string lexicographically",
    ),
    StageTestCase(
        "within_codewithscope_code_then_scope",
        docs=[
            {"_id": 1, "v": Code("f", {"x": 2})},
            {"_id": 2, "v": Code("f", {"x": 1})},
            {"_id": 3, "v": Code("g", {"x": 1})},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": Code("f", {"x": 1})},
            {"_id": 1, "v": Code("f", {"x": 2})},
            {"_id": 3, "v": Code("g", {"x": 1})},
        ],
        msg="$sort should sort CodeWithScope by code string first then by scope document",
    ),
    StageTestCase(
        "within_binary_same_subtype_length_then_bytes",
        docs=[
            {"_id": 1, "v": Binary(b"\xff", 0)},
            {"_id": 2, "v": Binary(b"\x00", 0)},
            {"_id": 3, "v": Binary(b"\x00\x01", 0)},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": b"\x00"},
            {"_id": 1, "v": b"\xff"},
            {"_id": 3, "v": b"\x00\x01"},
        ],
        msg=(
            "$sort should sort Binary within the same subtype by data length"
            " first then by data bytes"
        ),
    ),
    # Binary subtype ordering: 0 < 1 < 3 < 4 < 5 < 128 < 2.
    StageTestCase(
        "within_binary_subtype_order",
        docs=[
            {"_id": 1, "v": Binary(b"\x01" * 16, 0)},
            {"_id": 2, "v": Binary(b"\x01" * 16, 1)},
            {"_id": 3, "v": Binary(b"\x01" * 16, 2)},
            {"_id": 4, "v": Binary(b"\x01" * 16, 3)},
            {"_id": 5, "v": Binary(b"\x01" * 16, 4)},
            {"_id": 6, "v": Binary(b"\x01" * 16, 5)},
            {"_id": 7, "v": Binary(b"\x01" * 16, 128)},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 1, "v": b"\x01" * 16},
            {"_id": 2, "v": Binary(b"\x01" * 16, 1)},
            {"_id": 4, "v": Binary(b"\x01" * 16, 3)},
            {"_id": 5, "v": Binary(b"\x01" * 16, 4)},
            {"_id": 6, "v": Binary(b"\x01" * 16, 5)},
            {"_id": 7, "v": Binary(b"\x01" * 16, 128)},
            {"_id": 3, "v": Binary(b"\x01" * 16, 2)},
        ],
        msg="$sort should order Binary subtypes as 0 < 1 < 3 < 4 < 5 < 128 < 2",
    ),
    StageTestCase(
        "within_datetime_chronological_pre_epoch",
        docs=[
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "v": datetime(1969, 12, 31, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": datetime(1969, 12, 31)},
            {"_id": 1, "v": datetime(2024, 1, 1)},
        ],
        msg=(
            "$sort should sort datetime values chronologically"
            " with pre-epoch dates sorting correctly"
        ),
    ),
    StageTestCase(
        "within_datetime_millisecond_precision",
        docs=[
            {"_id": 1, "v": datetime(2024, 1, 1, 0, 0, 0, 2000, tzinfo=timezone.utc)},
            {"_id": 2, "v": datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": datetime(2024, 1, 1, 0, 0, 0, 1000)},
            {"_id": 1, "v": datetime(2024, 1, 1, 0, 0, 0, 2000)},
        ],
        msg="$sort should respect millisecond precision in datetime ordering",
    ),
    StageTestCase(
        "within_timestamp_time_then_increment",
        docs=[
            {"_id": 1, "v": Timestamp(100, 2)},
            {"_id": 2, "v": Timestamp(100, 1)},
            {"_id": 3, "v": Timestamp(200, 1)},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": Timestamp(100, 1)},
            {"_id": 1, "v": Timestamp(100, 2)},
            {"_id": 3, "v": Timestamp(200, 1)},
        ],
        msg="$sort should sort Timestamp by time component first then by increment",
    ),
]

SORT_TYPE_COMPARISON_TESTS = SORT_BSON_TYPE_ORDER_TESTS + SORT_WITHIN_TYPE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SORT_TYPE_COMPARISON_TESTS))
def test_sort_type_comparison(collection, test_case: StageTestCase):
    """Test $sort BSON type comparison ordering."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
