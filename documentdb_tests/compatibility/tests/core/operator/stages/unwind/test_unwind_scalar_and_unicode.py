"""Tests for $unwind stage — scalar passthrough and unicode field names."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

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

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Non-Array Scalar Passthrough]: when the value at the path is a
# non-array, non-null, non-missing scalar, $unwind outputs a single document
# with the value as-is, regardless of the preserveNullAndEmptyArrays setting.
UNWIND_SCALAR_PASSTHROUGH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "scalar_bool",
        docs=[{"_id": 1, "a": True}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": True}],
        msg="$unwind should pass through bool scalar as-is",
    ),
    StageTestCase(
        "scalar_int32",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through int32 scalar as-is",
    ),
    StageTestCase(
        "scalar_int64",
        docs=[{"_id": 1, "a": Int64(999)}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Int64(999)}],
        msg="$unwind should pass through Int64 scalar as-is",
    ),
    StageTestCase(
        "scalar_double",
        docs=[{"_id": 1, "a": 3.14}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 3.14}],
        msg="$unwind should pass through double scalar as-is",
    ),
    StageTestCase(
        "scalar_decimal128",
        docs=[{"_id": 1, "a": Decimal128("9.99")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Decimal128("9.99")}],
        msg="$unwind should pass through Decimal128 scalar as-is",
    ),
    StageTestCase(
        "scalar_string",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$unwind should pass through string scalar as-is",
    ),
    StageTestCase(
        "scalar_object",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": {"x": 1}}],
        msg="$unwind should pass through embedded document scalar as-is",
    ),
    StageTestCase(
        "scalar_objectid",
        docs=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        msg="$unwind should pass through ObjectId scalar as-is",
    ),
    StageTestCase(
        "scalar_datetime",
        docs=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$unwind should pass through datetime scalar as-is",
    ),
    StageTestCase(
        "scalar_timestamp",
        docs=[{"_id": 1, "a": Timestamp(1, 1)}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Timestamp(1, 1)}],
        msg="$unwind should pass through Timestamp scalar as-is",
    ),
    StageTestCase(
        "scalar_binary",
        docs=[{"_id": 1, "a": Binary(b"\x01\x02")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": b"\x01\x02"}],
        msg="$unwind should pass through Binary scalar as-is",
    ),
    StageTestCase(
        "scalar_binary_uuid",
        docs=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            }
        ],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            }
        ],
        msg="$unwind should pass through Binary UUID scalar as-is",
    ),
    StageTestCase(
        "scalar_regex",
        docs=[{"_id": 1, "a": Regex("^a", "i")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Regex("^a", "i")}],
        msg="$unwind should pass through Regex scalar as-is",
    ),
    StageTestCase(
        "scalar_code",
        docs=[{"_id": 1, "a": Code("x")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Code("x")}],
        msg="$unwind should pass through Code scalar as-is",
    ),
    StageTestCase(
        "scalar_minkey",
        docs=[{"_id": 1, "a": MinKey()}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": MinKey()}],
        msg="$unwind should pass through MinKey scalar as-is",
    ),
    StageTestCase(
        "scalar_maxkey",
        docs=[{"_id": 1, "a": MaxKey()}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="$unwind should pass through MaxKey scalar as-is",
    ),
    StageTestCase(
        "scalar_preserve_true_does_not_affect",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through scalar as-is when preserveNullAndEmptyArrays is true",
    ),
    StageTestCase(
        "scalar_preserve_false_does_not_affect",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through scalar as-is when preserveNullAndEmptyArrays is false",
    ),
]

# Property [Unicode No Normalization]: precomposed and decomposed Unicode forms
# are treated as distinct field names with no normalization, for both the path
# and includeArrayIndex field names; special characters are accepted in field
# names referenced by the path.
UNWIND_UNICODE_ENCODING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unicode_precomposed_path_distinct_from_decomposed",
        docs=[{"_id": 1, "\u00e9": [1, 2], "e\u0301": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$\u00e9"}}],
        expected=[
            {"_id": 1, "\u00e9": 1, "e\u0301": [10, 20]},
            {"_id": 1, "\u00e9": 2, "e\u0301": [10, 20]},
        ],
        msg=(
            "$unwind on precomposed path should only unwind that field"
            " and leave the decomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_decomposed_path_distinct_from_precomposed",
        docs=[{"_id": 1, "\u00e9": [1, 2], "e\u0301": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$e\u0301"}}],
        expected=[
            {"_id": 1, "\u00e9": [1, 2], "e\u0301": 10},
            {"_id": 1, "\u00e9": [1, 2], "e\u0301": 20},
        ],
        msg=(
            "$unwind on decomposed path should only unwind that field"
            " and leave the precomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_precomposed_index_distinct_from_decomposed",
        docs=[{"_id": 1, "a": [10, 20], "\u00e9": "pre", "e\u0301": "dec"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "\u00e9"}}],
        expected=[
            {"_id": 1, "a": 10, "\u00e9": INT64_ZERO, "e\u0301": "dec"},
            {"_id": 1, "a": 20, "\u00e9": Int64(1), "e\u0301": "dec"},
        ],
        msg=(
            "includeArrayIndex with precomposed name should overwrite only"
            " the precomposed field and leave the decomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_decomposed_index_distinct_from_precomposed",
        docs=[{"_id": 1, "a": [10, 20], "\u00e9": "pre", "e\u0301": "dec"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "e\u0301"}}],
        expected=[
            {"_id": 1, "a": 10, "\u00e9": "pre", "e\u0301": INT64_ZERO},
            {"_id": 1, "a": 20, "\u00e9": "pre", "e\u0301": Int64(1)},
        ],
        msg=(
            "includeArrayIndex with decomposed name should overwrite only"
            " the decomposed field and leave the precomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_space_in_path",
        docs=[{"_id": 1, "a b": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a b"}}],
        expected=[{"_id": 1, "a b": 1}, {"_id": 1, "a b": 2}],
        msg="$unwind should accept space in path field name",
    ),
    StageTestCase(
        "unicode_tab_in_path",
        docs=[{"_id": 1, "a\tb": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a\tb"}}],
        expected=[{"_id": 1, "a\tb": 1}, {"_id": 1, "a\tb": 2}],
        msg="$unwind should accept tab in path field name",
    ),
    StageTestCase(
        "unicode_nbsp_in_path",
        docs=[{"_id": 1, "a\u00a0b": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a\u00a0b"}}],
        expected=[{"_id": 1, "a\u00a0b": 1}, {"_id": 1, "a\u00a0b": 2}],
        msg="$unwind should accept NBSP in path field name",
    ),
    StageTestCase(
        "unicode_control_char_in_path",
        docs=[{"_id": 1, "a\x01b": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a\x01b"}}],
        expected=[{"_id": 1, "a\x01b": 1}, {"_id": 1, "a\x01b": 2}],
        msg="$unwind should accept control character in path field name",
    ),
    StageTestCase(
        "unicode_emoji_in_path",
        docs=[{"_id": 1, "\U0001f389": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$\U0001f389"}}],
        expected=[{"_id": 1, "\U0001f389": 1}, {"_id": 1, "\U0001f389": 2}],
        msg="$unwind should accept emoji in path field name",
    ),
    StageTestCase(
        "unicode_zwj_sequence_in_path",
        docs=[{"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$\U0001f468\u200d\U0001f469\u200d\U0001f467"}}],
        expected=[
            {"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": 1},
            {"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": 2},
        ],
        msg="$unwind should accept ZWJ sequence in path field name",
    ),
]

UNWIND_SCALAR_AND_UNICODE_TESTS = UNWIND_SCALAR_PASSTHROUGH_TESTS + UNWIND_UNICODE_ENCODING_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_SCALAR_AND_UNICODE_TESTS))
def test_unwind_scalar_and_unicode(collection, test_case: StageTestCase):
    """Test $unwind scalar passthrough and unicode field names."""
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
        ignore_doc_order=True,
    )
