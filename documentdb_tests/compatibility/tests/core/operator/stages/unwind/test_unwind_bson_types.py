"""Tests for $unwind stage — BSON type preservation."""

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

# Property [BSON Type Preservation]: all BSON types representable by pymongo
# are preserved exactly when unwound from array elements.
UNWIND_BSON_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "bson_bool",
        docs=[{"_id": 1, "a": [True, False]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": True}, {"_id": 1, "a": False}],
        msg="$unwind should preserve bool elements",
    ),
    StageTestCase(
        "bson_int32",
        docs=[{"_id": 1, "a": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 1}, {"_id": 1, "a": 2}],
        msg="$unwind should preserve int32 elements",
    ),
    StageTestCase(
        "bson_int64",
        docs=[{"_id": 1, "a": [Int64(100), Int64(200)]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Int64(100)}, {"_id": 1, "a": Int64(200)}],
        msg="$unwind should preserve Int64 elements",
    ),
    StageTestCase(
        "bson_double",
        docs=[{"_id": 1, "a": [1.5, 2.5]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 1.5}, {"_id": 1, "a": 2.5}],
        msg="$unwind should preserve double elements",
    ),
    StageTestCase(
        "bson_decimal128",
        docs=[{"_id": 1, "a": [Decimal128("1.1"), Decimal128("2.2")]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": Decimal128("1.1")},
            {"_id": 1, "a": Decimal128("2.2")},
        ],
        msg="$unwind should preserve Decimal128 elements",
    ),
    StageTestCase(
        "bson_string",
        docs=[{"_id": 1, "a": ["hello", "world"]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": "hello"}, {"_id": 1, "a": "world"}],
        msg="$unwind should preserve string elements",
    ),
    StageTestCase(
        "bson_object",
        docs=[{"_id": 1, "a": [{"x": 1}, {"y": 2}]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": {"x": 1}}, {"_id": 1, "a": {"y": 2}}],
        msg="$unwind should preserve embedded document elements",
    ),
    StageTestCase(
        "bson_objectid",
        docs=[
            {
                "_id": 1,
                "a": [
                    ObjectId("000000000000000000000001"),
                    ObjectId("000000000000000000000002"),
                ],
            }
        ],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": ObjectId("000000000000000000000001")},
            {"_id": 1, "a": ObjectId("000000000000000000000002")},
        ],
        msg="$unwind should preserve ObjectId elements",
    ),
    StageTestCase(
        "bson_datetime",
        docs=[
            {
                "_id": 1,
                "a": [
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                    datetime(2025, 6, 15, tzinfo=timezone.utc),
                ],
            }
        ],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 1, "a": datetime(2025, 6, 15, tzinfo=timezone.utc)},
        ],
        msg="$unwind should preserve datetime elements",
    ),
    StageTestCase(
        "bson_timestamp",
        docs=[{"_id": 1, "a": [Timestamp(1, 1), Timestamp(2, 2)]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": Timestamp(1, 1)},
            {"_id": 1, "a": Timestamp(2, 2)},
        ],
        msg="$unwind should preserve Timestamp elements",
    ),
    StageTestCase(
        "bson_binary",
        docs=[{"_id": 1, "a": [Binary(b"\x01"), Binary(b"\x02")]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": b"\x01"},
            {"_id": 1, "a": b"\x02"},
        ],
        msg="$unwind should preserve Binary elements",
    ),
    StageTestCase(
        "bson_binary_uuid",
        docs=[
            {
                "_id": 1,
                "a": [
                    Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
                    Binary.from_uuid(UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")),
                ],
            }
        ],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            },
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")),
            },
        ],
        msg="$unwind should preserve Binary UUID elements",
    ),
    StageTestCase(
        "bson_regex",
        docs=[{"_id": 1, "a": [Regex("^a", "i"), Regex("^b")]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": Regex("^a", "i")},
            {"_id": 1, "a": Regex("^b")},
        ],
        msg="$unwind should preserve Regex elements",
    ),
    StageTestCase(
        "bson_code",
        docs=[{"_id": 1, "a": [Code("x"), Code("y")]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Code("x")}, {"_id": 1, "a": Code("y")}],
        msg="$unwind should preserve Code elements",
    ),
    StageTestCase(
        "bson_minkey",
        docs=[{"_id": 1, "a": [MinKey(), 1]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": MinKey()}, {"_id": 1, "a": 1}],
        msg="$unwind should preserve MinKey elements",
    ),
    StageTestCase(
        "bson_maxkey",
        docs=[{"_id": 1, "a": [MaxKey(), 1]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": MaxKey()}, {"_id": 1, "a": 1}],
        msg="$unwind should preserve MaxKey elements",
    ),
    StageTestCase(
        "bson_null_element",
        docs=[{"_id": 1, "a": [None, 1]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": None}, {"_id": 1, "a": 1}],
        msg="$unwind should preserve null elements within an array",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_BSON_TYPE_TESTS))
def test_unwind_bson_types(collection, test_case: StageTestCase):
    """Test $unwind BSON type preservation."""
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
