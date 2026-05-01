"""Tests for $unwind stage — multi-stage chaining."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Multi-Stage Unwind]: chaining multiple $unwind stages composes
# correctly with independent state tracking, cross-product semantics, and
# preserve interactions.
UNWIND_MULTI_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multi_stage_index_resets_per_subarray",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[
            {"$unwind": {"path": "$a", "includeArrayIndex": "i1"}},
            {"$unwind": {"path": "$a", "includeArrayIndex": "i2"}},
        ],
        expected=[
            {"_id": 1, "a": 10, "i1": INT64_ZERO, "i2": INT64_ZERO},
            {"_id": 1, "a": 20, "i1": INT64_ZERO, "i2": Int64(1)},
            {"_id": 1, "a": 30, "i1": Int64(1), "i2": INT64_ZERO},
        ],
        msg=(
            "Second $unwind includeArrayIndex should reset to 0 for each"
            " sub-array produced by the first $unwind"
        ),
    ),
    StageTestCase(
        "multi_stage_cross_product_different_fields",
        docs=[{"_id": 1, "a": [1, 2], "b": ["x", "y"]}],
        pipeline=[{"$unwind": {"path": "$a"}}, {"$unwind": {"path": "$b"}}],
        expected=[
            {"_id": 1, "a": 1, "b": "x"},
            {"_id": 1, "a": 1, "b": "y"},
            {"_id": 1, "a": 2, "b": "x"},
            {"_id": 1, "a": 2, "b": "y"},
        ],
        msg=(
            "Two $unwind stages on different array fields should produce"
            " a cross product of elements"
        ),
    ),
    StageTestCase(
        "multi_stage_preserve_first_filter_second",
        docs=[
            {"_id": 1, "a": [1, 2], "b": ["x"]},
            {"_id": 2, "a": [3], "b": None},
            {"_id": 3, "a": [4]},
            {"_id": 4, "a": None, "b": ["z"]},
        ],
        pipeline=[
            {"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$b", "preserveNullAndEmptyArrays": False}},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": "x"},
            {"_id": 1, "a": 2, "b": "x"},
            {"_id": 4, "a": None, "b": "z"},
        ],
        msg=(
            "preserveNullAndEmptyArrays on first $unwind followed by false"
            " on second should filter documents where second path is null or missing"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_MULTI_STAGE_TESTS))
def test_unwind_multi_stage(collection, test_case: StageTestCase):
    """Test $unwind multi-stage chaining."""
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
