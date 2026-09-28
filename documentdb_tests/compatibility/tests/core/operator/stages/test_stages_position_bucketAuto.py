"""Tests for $bucketAuto composing with other stages in common use cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Composition]: $bucketAuto composes correctly with other
# stages in realistic multi-stage pipelines.
BUCKET_AUTO_PIPELINE_COMPOSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_before_bucketAuto",
        docs=[
            {"_id": 1, "status": "active", "score": 15},
            {"_id": 2, "status": "inactive", "score": 25},
            {"_id": 3, "status": "active", "score": 35},
            {"_id": 4, "status": "active", "score": 45},
        ],
        pipeline=[
            {"$match": {"status": "active"}},
            {"$bucketAuto": {"groupBy": "$score", "buckets": 2}},
        ],
        expected=[
            {"_id": {"min": 15, "max": 45}, "count": 2},
            {"_id": {"min": 45, "max": 45}, "count": 1},
        ],
        msg="$bucketAuto should operate on documents filtered by a preceding $match",
    ),
    StageTestCase(
        "sort_after_bucketAuto",
        docs=[{"_id": i, "x": i} for i in range(1, 5)],
        pipeline=[
            {"$bucketAuto": {"groupBy": "$x", "buckets": 2}},
            {"$sort": {"_id.min": -1}},
        ],
        expected=[
            {"_id": {"min": 3, "max": 4}, "count": 2},
            {"_id": {"min": 1, "max": 3}, "count": 2},
        ],
        msg="$bucketAuto output should be sortable by a following $sort on the bucket _id",
    ),
    StageTestCase(
        "limit_after_bucketAuto",
        docs=[{"_id": i, "x": i} for i in range(1, 7)],
        pipeline=[
            {"$bucketAuto": {"groupBy": "$x", "buckets": 3}},
            {"$limit": 2},
        ],
        expected=[
            {"_id": {"min": 1, "max": 3}, "count": 2},
            {"_id": {"min": 3, "max": 5}, "count": 2},
        ],
        msg="$limit should truncate $bucketAuto output",
    ),
    StageTestCase(
        "skip_after_bucketAuto",
        docs=[{"_id": i, "x": i} for i in range(1, 7)],
        pipeline=[
            {"$bucketAuto": {"groupBy": "$x", "buckets": 3}},
            {"$skip": 1},
        ],
        expected=[
            {"_id": {"min": 3, "max": 5}, "count": 2},
            {"_id": {"min": 5, "max": 6}, "count": 2},
        ],
        msg="$skip should skip $bucketAuto output buckets",
    ),
    StageTestCase(
        "facet_multiple_bucketAuto",
        docs=[{"_id": 1, "x": 5, "y": 50}, {"_id": 2, "x": 15, "y": 150}],
        pipeline=[
            {
                "$facet": {
                    "byX": [{"$bucketAuto": {"groupBy": "$x", "buckets": 1}}],
                    "byY": [{"$bucketAuto": {"groupBy": "$y", "buckets": 1}}],
                }
            }
        ],
        expected=[
            {
                "byX": [{"_id": {"min": 5, "max": 15}, "count": 2}],
                "byY": [{"_id": {"min": 50, "max": 150}, "count": 2}],
            }
        ],
        msg="$bucketAuto should run inside multiple $facet sub-pipelines over different fields",
    ),
    StageTestCase(
        "group_after_bucketAuto",
        docs=[{"_id": i, "x": i} for i in range(1, 7)],
        pipeline=[
            {"$bucketAuto": {"groupBy": "$x", "buckets": 3}},
            {"$group": {"_id": None, "avg_count": {"$avg": "$count"}}},
        ],
        expected=[{"_id": None, "avg_count": 2.0}],
        msg="$group should aggregate across $bucketAuto output",
    ),
    StageTestCase(
        "project_after_bucketAuto",
        docs=[
            {"_id": 1, "x": 5, "v": 10},
            {"_id": 2, "x": 5, "v": 20},
            {"_id": 3, "x": 15, "v": 30},
        ],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 2,
                    "output": {"total": {"$sum": "$v"}, "n": {"$sum": 1}},
                }
            },
            {"$project": {"avg": {"$divide": ["$total", "$n"]}}},
        ],
        expected=[
            {"_id": {"min": 5, "max": 15}, "avg": 15.0},
            {"_id": {"min": 15, "max": 15}, "avg": 30.0},
        ],
        msg="$project should compute on fields produced by $bucketAuto",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_PIPELINE_COMPOSITION_TESTS))
def test_bucketAuto_pipeline_composition(collection, test_case: StageTestCase):
    """Test $bucketAuto composing with other stages in common use cases."""
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
