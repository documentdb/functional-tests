"""Aggregation $facet stage tests - BSON type pass-through.

Verifies that $facet passes documents of every standard BSON type through to
sub-pipelines without altering their values (TEST_COVERAGE.md §1 Data Type
Coverage, applied to the pass-through behaviour of the stage).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Pass-Through]: $facet preserves one document of each standard
# BSON type inside its sub-pipelines.
FACET_BSON_PASSTHROUGH_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="int32",
        docs=[{"_id": 1, "val": 42}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": 42}]}],
        msg="$facet should pass an int32 value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="int64",
        docs=[{"_id": 1, "val": Int64(42)}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": Int64(42)}]}],
        msg="$facet should pass an int64 value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="double",
        docs=[{"_id": 1, "val": 1.5}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": 1.5}]}],
        msg="$facet should pass a double value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="decimal128",
        docs=[{"_id": 1, "val": Decimal128("1.5")}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": Decimal128("1.5")}]}],
        msg="$facet should pass a decimal128 value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="string",
        docs=[{"_id": 1, "val": "hello"}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": "hello"}]}],
        msg="$facet should pass a string value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="bool",
        docs=[{"_id": 1, "val": True}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": True}]}],
        msg="$facet should pass a boolean value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="date",
        docs=[{"_id": 1, "val": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": datetime(2024, 1, 1, tzinfo=timezone.utc)}]}],
        msg="$facet should pass a date value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="null",
        docs=[{"_id": 1, "val": None}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": None}]}],
        msg="$facet should pass a null value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="object",
        docs=[{"_id": 1, "val": {"a": 1, "b": {"c": 2}}}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": {"a": 1, "b": {"c": 2}}}]}],
        msg="$facet should pass an object value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="array",
        docs=[{"_id": 1, "val": [1, "two", 3.0]}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": [1, "two", 3.0]}]}],
        msg="$facet should pass an array value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="objectId",
        docs=[{"_id": 1, "val": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": ObjectId("507f1f77bcf86cd799439011")}]}],
        msg="$facet should pass an objectId value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="binData",
        docs=[{"_id": 1, "val": Binary(b"payload", 128)}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": Binary(b"payload", 128)}]}],
        msg="$facet should pass a binary value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="timestamp",
        docs=[{"_id": 1, "val": Timestamp(123, 4)}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": Timestamp(123, 4)}]}],
        msg="$facet should pass a timestamp value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="minKey",
        docs=[{"_id": 1, "val": MinKey()}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": MinKey()}]}],
        msg="$facet should pass a minKey value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="maxKey",
        docs=[{"_id": 1, "val": MaxKey()}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": MaxKey()}]}],
        msg="$facet should pass a maxKey value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="regex",
        docs=[{"_id": 1, "val": Regex(r"^hello", "i")}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": Regex(r"^hello", "i")}]}],
        msg="$facet should pass a regex value through to sub-pipelines unchanged",
    ),
    StageTestCase(
        id="javascript",
        docs=[{"_id": 1, "val": Code("function() {}")}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "val": Code("function() {}")}]}],
        msg="$facet should pass a javascript value through to sub-pipelines unchanged",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_BSON_PASSTHROUGH_TESTS))
def test_facet_bson_passthrough(collection, test_case: StageTestCase):
    """$facet passes a document field of each BSON type through unchanged."""
    coll = populate_collection(collection, test_case)
    command: dict[str, Any] = {
        "aggregate": coll.name,
        "pipeline": test_case.pipeline,
        "cursor": {},
    }
    command.update(test_case.extra_command_fields)
    result = execute_command(coll, command)
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=test_case.ignore_doc_order,
        ignore_order_in=test_case.ignore_order_in,
    )
