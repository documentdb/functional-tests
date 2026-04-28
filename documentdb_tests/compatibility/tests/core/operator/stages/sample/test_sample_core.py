"""Tests for $sample stage core behavior."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Core Count]: $sample returns exactly N documents when the
# collection has at least N, and all documents when fewer than N are available.
SAMPLE_CORE_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_exact_n",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 3}}, {"$count": "n"}],
        expected=[{"n": 3}],
        msg="$sample should return exactly N documents when collection has at least N",
    ),
    StageTestCase(
        "count_size_equals_collection",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 5}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should return all documents when size equals collection count",
    ),
    StageTestCase(
        "count_size_exceeds_collection",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 10}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should return all documents when size exceeds collection count",
    ),
    StageTestCase(
        "count_empty_collection",
        docs=[],
        pipeline=[{"$sample": {"size": 3}}, {"$count": "n"}],
        expected=[],
        msg="$sample should return zero documents from an empty collection",
    ),
    StageTestCase(
        "count_nonexistent_collection",
        docs=None,
        pipeline=[{"$sample": {"size": 3}}, {"$count": "n"}],
        expected=[],
        msg="$sample should return zero documents from a non-existent collection",
    ),
    StageTestCase(
        "count_preceding_stage_zero",
        docs=[{"_id": i, "v": i} for i in range(5)],
        pipeline=[{"$match": {"v": 999}}, {"$sample": {"size": 3}}, {"$count": "n"}],
        expected=[],
        msg="$sample should return zero documents when a preceding stage produces none",
    ),
    StageTestCase(
        "returns_actual_documents",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}, {"_id": 3, "v": "c"}],
        pipeline=[{"$sample": {"size": 3}}],
        expected=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}, {"_id": 3, "v": "c"}],
        msg="$sample should return the actual documents from the collection",
    ),
    StageTestCase(
        "position_multiple_sample_stages",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$sample": {"size": 3}},
            {"$sample": {"size": 5}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample followed by $sample should operate on the previous stage's output",
    ),
]

# Property [Structure Preservation]: sampled documents retain their original
# structure including nested objects, arrays, and all BSON types.
SAMPLE_STRUCTURE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "structure_all_bson_types",
        docs=[
            {
                "_id": 1,
                "double": 3.14,
                "string": "hello",
                "object": {"a": {"b": 1}},
                "array": [1, "two", 3.0],
                "binary": b"\x01\x02",
                "binary_uuid": Binary.from_uuid(UUID("12345678-1234-5678-1234-567812345678")),
                "objectid": ObjectId("507f1f77bcf86cd799439011"),
                "boolean": True,
                "datetime": datetime(2023, 1, 1),
                "null": None,
                "regex": Regex("abc", 2),
                "javascript": Code("function(){}"),
                "javascript_scope": Code("function(){return x}", {"x": 1}),
                "int32": 42,
                "timestamp": Timestamp(1234567890, 1),
                "int64": Int64(2**40),
                "decimal128": DECIMAL128_ONE_AND_HALF,
                "minkey": MinKey(),
                "maxkey": MaxKey(),
            }
        ],
        pipeline=[{"$sample": {"size": 1}}],
        expected=[
            {
                "_id": 1,
                "double": 3.14,
                "string": "hello",
                "object": {"a": {"b": 1}},
                "array": [1, "two", 3.0],
                "binary": b"\x01\x02",
                "binary_uuid": Binary.from_uuid(UUID("12345678-1234-5678-1234-567812345678")),
                "objectid": ObjectId("507f1f77bcf86cd799439011"),
                "boolean": True,
                "datetime": datetime(2023, 1, 1),
                "null": None,
                "regex": Regex("abc", 2),
                "javascript": Code("function(){}"),
                "javascript_scope": Code("function(){return x}", {"x": 1}),
                "int32": 42,
                "timestamp": Timestamp(1234567890, 1),
                "int64": Int64(2**40),
                "decimal128": DECIMAL128_ONE_AND_HALF,
                "minkey": MinKey(),
                "maxkey": MaxKey(),
            }
        ],
        msg="$sample should preserve all BSON types representable by pymongo",
    ),
]

# Property [No Duplicates]: the result set contains no duplicate documents,
# even when size approaches or exceeds the collection count.
SAMPLE_NO_DUPLICATES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "no_dup_size_equals_count",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$sample": {"size": 10}},
            {"$group": {"_id": "$_id"}},
            {"$count": "n"},
        ],
        expected=[{"n": 10}],
        msg="$sample should return no duplicates when size equals collection count",
    ),
    StageTestCase(
        "no_dup_size_one_less",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$sample": {"size": 9}},
            {"$group": {"_id": "$_id"}},
            {"$count": "n"},
        ],
        expected=[{"n": 9}],
        msg="$sample should return no duplicates when size is one less than collection count",
    ),
    StageTestCase(
        "no_dup_size_far_exceeds_count",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$sample": {"size": 1000}},
            {"$group": {"_id": "$_id"}},
            {"$count": "n"},
        ],
        expected=[{"n": 10}],
        msg="$sample should return no duplicates when size far exceeds collection count",
    ),
]

SAMPLE_CORE_TESTS = SAMPLE_CORE_COUNT_TESTS + SAMPLE_STRUCTURE_TESTS + SAMPLE_NO_DUPLICATES_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SAMPLE_CORE_TESTS))
def test_sample_core(collection, test_case: StageTestCase):
    """Test $sample stage core behavior."""
    if test_case.setup:
        test_case.setup(collection)
    if test_case.docs:
        collection.insert_many(test_case.docs)
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
