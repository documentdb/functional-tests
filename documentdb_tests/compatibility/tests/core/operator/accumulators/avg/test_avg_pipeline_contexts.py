"""
Tests for $avg in various pipeline contexts.

Covers $group, $bucket, $setWindowFields, $project/$addFields,
$match+$expr, and pipeline interaction patterns.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- $group with computed _id ---

# Property [Group Computed ID]: $avg with computed _id expression in $group.
AVG_GROUP_COMPUTED_ID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "group_computed_id",
        docs=[
            {"_id": 1, "value": 10, "score": 80},
            {"_id": 2, "value": 20, "score": 90},
            {"_id": 3, "value": 30, "score": 85},
            {"_id": 4, "value": 40, "score": 95},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": {"$gt": ["$score", 85]},
                    "avg": {"$avg": "$value"},
                }
            },
            {"$sort": {"_id": 1}},
        ],
        # score <= 85: docs 1,3 -> avg(10,30) = 20
        # score > 85: docs 2,4 -> avg(20,40) = 30
        expected=[
            {"_id": False, "avg": 20.0},
            {"_id": True, "avg": 30.0},
        ],
        msg="$avg with computed _id should group and average correctly",
    ),
]

# --- $bucket / $bucketAuto ---

# Property [Bucket]: $avg in $bucket and $bucketAuto output specifications.
AVG_BUCKET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket",
        docs=[
            {"_id": 1, "score": 15, "value": 10},
            {"_id": 2, "score": 25, "value": 20},
            {"_id": 3, "score": 35, "value": 30},
            {"_id": 4, "score": 45, "value": 40},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$score",
                    "boundaries": [0, 20, 40, 60],
                    "output": {"avg_value": {"$avg": "$value"}},
                }
            },
        ],
        expected=[
            {"_id": 0, "avg_value": 10.0},
            {"_id": 20, "avg_value": 25.0},
            {"_id": 40, "avg_value": 40.0},
        ],
        msg="$avg in $bucket should compute average per bucket",
    ),
    AccumulatorTestCase(
        "bucketauto",
        docs=[
            {"_id": 1, "score": 10, "value": 100},
            {"_id": 2, "score": 20, "value": 200},
            {"_id": 3, "score": 30, "value": 300},
            {"_id": 4, "score": 40, "value": 400},
        ],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$score",
                    "buckets": 2,
                    "output": {"avg_value": {"$avg": "$value"}},
                }
            },
        ],
        expected=[
            {"_id": {"min": 10, "max": 30}, "avg_value": 150.0},
            {"_id": {"min": 30, "max": 40}, "avg_value": 350.0},
        ],
        msg="$avg in $bucketAuto should compute average per auto-bucket",
    ),
]

# --- $setWindowFields ---

# Property [Window]: $avg in $setWindowFields with various window types.
AVG_WINDOW_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "window_unbounded",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$setWindowFields": {
                    "sortBy": {"_id": 1},
                    "output": {
                        "avg": {
                            "$avg": "$value",
                            "window": {"documents": ["unbounded", "unbounded"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "value": 1, "avg": 1}},
        ],
        expected=[
            {"_id": 1, "value": 10, "avg": 20.0},
            {"_id": 2, "value": 20, "avg": 20.0},
            {"_id": 3, "value": 30, "avg": 20.0},
        ],
        msg="$avg with unbounded window should return full partition average",
    ),
    AccumulatorTestCase(
        "window_cumulative",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$setWindowFields": {
                    "sortBy": {"_id": 1},
                    "output": {
                        "avg": {
                            "$avg": "$value",
                            "window": {"documents": ["unbounded", "current"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "value": 1, "avg": 1}},
        ],
        expected=[
            {"_id": 1, "value": 10, "avg": 10.0},
            {"_id": 2, "value": 20, "avg": 15.0},
            {"_id": 3, "value": 30, "avg": 20.0},
        ],
        msg="$avg with cumulative window should compute running average",
    ),
    AccumulatorTestCase(
        "window_sliding",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
            {"_id": 4, "value": 40},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$setWindowFields": {
                    "sortBy": {"_id": 1},
                    "output": {
                        "avg": {
                            "$avg": "$value",
                            "window": {"documents": [-1, 1]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "value": 1, "avg": 1}},
        ],
        # avg(10,20), avg(10,20,30), avg(20,30,40), avg(30,40)
        expected=[
            {"_id": 1, "value": 10, "avg": 15.0},
            {"_id": 2, "value": 20, "avg": 20.0},
            {"_id": 3, "value": 30, "avg": 30.0},
            {"_id": 4, "value": 40, "avg": 35.0},
        ],
        msg="$avg with sliding window should compute local average",
    ),
    AccumulatorTestCase(
        "window_current_only",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$setWindowFields": {
                    "sortBy": {"_id": 1},
                    "output": {
                        "avg": {
                            "$avg": "$value",
                            "window": {"documents": [0, 0]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "value": 1, "avg": 1}},
        ],
        expected=[
            {"_id": 1, "value": 10, "avg": 10.0},
            {"_id": 2, "value": 20, "avg": 20.0},
            {"_id": 3, "value": 30, "avg": 30.0},
        ],
        msg="$avg with [0,0] window should return current document value",
    ),
    AccumulatorTestCase(
        "window_with_nulls",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": None},
            {"_id": 3, "value": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$setWindowFields": {
                    "sortBy": {"_id": 1},
                    "output": {
                        "avg": {
                            "$avg": "$value",
                            "window": {"documents": ["unbounded", "unbounded"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "value": 1, "avg": 1}},
        ],
        expected=[
            {"_id": 1, "value": 10, "avg": 20.0},
            {"_id": 2, "value": None, "avg": 20.0},
            {"_id": 3, "value": 30, "avg": 20.0},
        ],
        msg="$avg in window should ignore null values",
    ),
    AccumulatorTestCase(
        "window_range_based",
        docs=[
            {"_id": 1, "pos": 0, "value": 10},
            {"_id": 2, "pos": 5, "value": 20},
            {"_id": 3, "pos": 10, "value": 30},
            {"_id": 4, "pos": 15, "value": 40},
        ],
        pipeline=[
            {"$sort": {"pos": 1}},
            {
                "$setWindowFields": {
                    "sortBy": {"pos": 1},
                    "output": {
                        "avg": {
                            "$avg": "$value",
                            "window": {"range": [-5, 5]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "pos": 1, "value": 1, "avg": 1}},
        ],
        # pos=0: range [-5,5] includes pos 0,5 -> avg(10,20)=15
        # pos=5: range [0,10] includes pos 0,5,10 -> avg(10,20,30)=20
        # pos=10: range [5,15] includes pos 5,10,15 -> avg(20,30,40)=30
        # pos=15: range [10,20] includes pos 10,15 -> avg(30,40)=35
        expected=[
            {"_id": 1, "pos": 0, "value": 10, "avg": 15.0},
            {"_id": 2, "pos": 5, "value": 20, "avg": 20.0},
            {"_id": 3, "pos": 10, "value": 30, "avg": 30.0},
            {"_id": 4, "pos": 15, "value": 40, "avg": 35.0},
        ],
        msg="$avg with range-based window should compute average within range",
    ),
    AccumulatorTestCase(
        "window_multiple_partitions",
        docs=[
            {"_id": 1, "group": "A", "value": 10},
            {"_id": 2, "group": "A", "value": 20},
            {"_id": 3, "group": "A", "value": 30},
            {"_id": 4, "group": "B", "value": 100},
            {"_id": 5, "group": "B", "value": 200},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$setWindowFields": {
                    "partitionBy": "$group",
                    "sortBy": {"_id": 1},
                    "output": {
                        "avg": {
                            "$avg": "$value",
                            "window": {"documents": ["unbounded", "unbounded"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "group": 1, "avg": 1}},
        ],
        expected=[
            {"_id": 1, "group": "A", "avg": 20.0},
            {"_id": 2, "group": "A", "avg": 20.0},
            {"_id": 3, "group": "A", "avg": 20.0},
            {"_id": 4, "group": "B", "avg": 150.0},
            {"_id": 5, "group": "B", "avg": 150.0},
        ],
        msg="$avg should compute independent averages per partition",
    ),
]

# --- Expression contexts ($project, $addFields, $match+$expr) ---

# Property [Expression Context]: $avg used in expression contexts.
AVG_EXPRESSION_CONTEXT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "in_addfields",
        docs=[
            {"_id": 1, "scores": [80, 90, 100]},
        ],
        pipeline=[
            {"$addFields": {"avg_score": {"$avg": "$scores"}}},
            {"$project": {"_id": 0, "avg_score": 1}},
        ],
        expected=[{"avg_score": 90.0}],
        msg="$avg in $addFields should traverse array field and average",
    ),
    AccumulatorTestCase(
        "in_match_expr",
        docs=[
            {"_id": 1, "scores": [80, 90, 100]},
            {"_id": 2, "scores": [40, 50, 60]},
            {"_id": 3, "scores": [70, 80, 90]},
        ],
        pipeline=[
            {"$match": {"$expr": {"$gt": [{"$avg": "$scores"}, 75]}}},
            {"$project": {"_id": 1}},
            {"$sort": {"_id": 1}},
        ],
        # avg([80,90,100])=90 > 75, avg([40,50,60])=50 < 75, avg([70,80,90])=80 > 75
        expected=[{"_id": 1}, {"_id": 3}],
        msg="$avg in $match $expr should filter based on computed average",
    ),
]

# --- Pipeline interaction patterns ---

# Property [Pipeline Interaction]: $avg combined with other pipeline stages.
AVG_PIPELINE_INTERACTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "group_after_unwind",
        docs=[
            {"_id": 1, "category": "A", "values": [10, 20]},
            {"_id": 2, "category": "A", "values": [30]},
        ],
        pipeline=[
            {"$unwind": "$values"},
            {"$group": {"_id": "$category", "avg": {"$avg": "$values"}}},
        ],
        # Unwound: 10, 20, 30 -> avg = 20
        expected=[{"_id": "A", "avg": 20.0}],
        msg="$avg after $unwind should average all unwound values",
    ),
    AccumulatorTestCase(
        "group_after_match",
        docs=[
            {"_id": 1, "category": "A", "value": 10, "active": True},
            {"_id": 2, "category": "A", "value": 20, "active": False},
            {"_id": 3, "category": "A", "value": 30, "active": True},
        ],
        pipeline=[
            {"$match": {"active": True}},
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
        ],
        # Only active docs: avg(10, 30) = 20
        expected=[{"_id": "A", "avg": 20.0}],
        msg="$avg after $match should only average filtered documents",
    ),
    AccumulatorTestCase(
        "project_after_group",
        docs=[
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
            {"_id": 3, "category": "B", "value": 30},
            {"_id": 4, "category": "B", "value": 40},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$category",
                    "sum": {"$sum": "$value"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
            {
                "$project": {
                    "_id": 1,
                    "manual_avg": {"$divide": ["$sum", "$count"]},
                }
            },
        ],
        expected=[
            {"_id": "A", "manual_avg": 15.0},
            {"_id": "B", "manual_avg": 35.0},
        ],
        msg="Manual average via $divide after $group should work",
    ),
    AccumulatorTestCase(
        "group_after_project_rename",
        docs=[
            {"_id": 1, "cat": "A", "val": 10},
            {"_id": 2, "cat": "A", "val": 20},
        ],
        pipeline=[
            {"$project": {"category": "$cat", "value": "$val"}},
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
        ],
        expected=[{"_id": "A", "avg": 15.0}],
        msg="$avg should work on renamed fields from $project",
    ),
]

# --- Combined list ---

AVG_PIPELINE_CONTEXT_TESTS: list[AccumulatorTestCase] = (
    AVG_GROUP_COMPUTED_ID_TESTS
    + AVG_BUCKET_TESTS
    + AVG_WINDOW_TESTS
    + AVG_EXPRESSION_CONTEXT_TESTS
    + AVG_PIPELINE_INTERACTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_PIPELINE_CONTEXT_TESTS))
def test_avg_pipeline_contexts(collection, test_case: AccumulatorTestCase):
    """Test $avg in various pipeline contexts."""
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
    assertResult(result, expected=test_case.expected, msg=test_case.msg)


def test_avg_in_project_array_literal(collection):
    """Test $avg in $project with array of literal values.

    This test uses ``aggregate: 1`` with ``$documents`` instead of a
    collection, so it is kept as a standalone test.
    """
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "avg": {"$avg": [10, 20, 30]}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"avg": 20.0}],
        msg="$avg in $project with literal array should average values",
    )
