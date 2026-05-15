"""Tests for $bucket composing with other stages in common use cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Composition]: $bucket composes correctly with other
# stages in realistic multi-stage pipelines.
BUCKET_PIPELINE_COMPOSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_before_bucket",
        docs=[
            {"_id": 1, "status": "active", "score": 15},
            {"_id": 2, "status": "inactive", "score": 25},
            {"_id": 3, "status": "active", "score": 35},
            {"_id": 4, "status": "active", "score": 45},
        ],
        pipeline=[
            {"$match": {"status": "active"}},
            {
                "$bucket": {
                    "groupBy": "$score",
                    "boundaries": [0, 20, 40, 60],
                }
            },
        ],
        expected=[
            {"_id": 0, "count": 1},
            {"_id": 20, "count": 1},
            {"_id": 40, "count": 1},
        ],
        msg="$bucket should operate on documents filtered by a preceding $match",
    ),
    StageTestCase(
        "sort_after_bucket",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 15},
            {"_id": 3, "x": 25},
            {"_id": 4, "x": 5},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20, 30],
                    "output": {"total": {"$sum": 1}},
                }
            },
            {"$sort": {"total": -1, "_id": 1}},
        ],
        expected=[
            {"_id": 0, "total": 2},
            {"_id": 10, "total": 1},
            {"_id": 20, "total": 1},
        ],
        msg="$bucket output should be sortable by a following $sort",
    ),
    StageTestCase(
        "project_after_bucket",
        docs=[
            {"_id": 1, "x": 5, "v": 10},
            {"_id": 2, "x": 5, "v": 20},
            {"_id": 3, "x": 15, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20],
                    "output": {"total": {"$sum": "$v"}, "n": {"$sum": 1}},
                }
            },
            {"$project": {"avg": {"$divide": ["$total", "$n"]}}},
        ],
        expected=[
            {"_id": 0, "avg": 15.0},
            {"_id": 10, "avg": 30.0},
        ],
        msg="$project should compute on fields produced by $bucket",
    ),
    StageTestCase(
        "match_after_bucket",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 5},
            {"_id": 3, "x": 15},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10, 20]}},
            {"$match": {"count": {"$gt": 1}}},
        ],
        expected=[{"_id": 0, "count": 2}],
        msg="$match should filter $bucket output by accumulator values",
    ),
    StageTestCase(
        "limit_after_bucket",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 15},
            {"_id": 3, "x": 25},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10, 20, 30]}},
            {"$limit": 2},
        ],
        expected=[{"_id": 0, "count": 1}, {"_id": 10, "count": 1}],
        msg="$limit should truncate $bucket output",
    ),
    StageTestCase(
        "skip_after_bucket",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 15},
            {"_id": 3, "x": 25},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10, 20, 30]}},
            {"$skip": 1},
        ],
        expected=[{"_id": 10, "count": 1}, {"_id": 20, "count": 1}],
        msg="$skip should skip $bucket output buckets",
    ),
    StageTestCase(
        "unwind_push_after_bucket",
        docs=[
            {"_id": 1, "x": 5, "tag": "a"},
            {"_id": 2, "x": 5, "tag": "b"},
            {"_id": 3, "x": 15, "tag": "c"},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20],
                    "output": {"tags": {"$push": "$tag"}},
                }
            },
            {"$unwind": "$tags"},
            {"$sort": {"_id": 1, "tags": 1}},
        ],
        expected=[
            {"_id": 0, "tags": "a"},
            {"_id": 0, "tags": "b"},
            {"_id": 10, "tags": "c"},
        ],
        msg="$unwind should expand arrays produced by $bucket $push",
    ),
    StageTestCase(
        "bucket_on_computed_field",
        docs=[
            {"_id": 1, "price": 10, "qty": 2},
            {"_id": 2, "price": 20, "qty": 3},
            {"_id": 3, "price": 5, "qty": 10},
        ],
        pipeline=[
            {"$set": {"total": {"$multiply": ["$price", "$qty"]}}},
            {
                "$bucket": {
                    "groupBy": "$total",
                    "boundaries": [0, 50, 100],
                    "output": {"orders": {"$sum": 1}},
                }
            },
        ],
        expected=[
            {"_id": 0, "orders": 1},
            {"_id": 50, "orders": 2},
        ],
        msg="$bucket should group on a field computed by a preceding $set",
    ),
    StageTestCase(
        "count_after_bucket",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 15},
            {"_id": 3, "x": 25},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20, 30],
                }
            },
            {"$count": "num_buckets"},
        ],
        expected=[{"num_buckets": 3}],
        msg="$count should count the number of buckets produced by $bucket",
    ),
    StageTestCase(
        "group_after_bucket",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 5},
            {"_id": 3, "x": 15},
            {"_id": 4, "x": 25},
            {"_id": 5, "x": 25},
            {"_id": 6, "x": 25},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10, 20, 30]}},
            {"$group": {"_id": None, "avg_count": {"$avg": "$count"}}},
        ],
        expected=[{"_id": None, "avg_count": 2.0}],
        msg="$group should aggregate across $bucket output",
    ),
    StageTestCase(
        "replaceroot_before_bucket",
        docs=[
            {"_id": 1, "metrics": {"score": 15}},
            {"_id": 2, "metrics": {"score": 45}},
            {"_id": 3, "metrics": {"score": 75}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$metrics"}},
            {
                "$bucket": {
                    "groupBy": "$score",
                    "boundaries": [0, 30, 60, 100],
                }
            },
        ],
        expected=[
            {"_id": 0, "count": 1},
            {"_id": 30, "count": 1},
            {"_id": 60, "count": 1},
        ],
        msg="$bucket should operate on documents reshaped by $replaceRoot",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_PIPELINE_COMPOSITION_TESTS))
def test_bucket_pipeline_composition(collection, test_case: StageTestCase):
    """Test $bucket composing with other stages in common use cases."""
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
