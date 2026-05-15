"""Tests for $group composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $group works correctly when preceded by stages
# that filter, reshape, or reorder documents.
GROUP_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="group_after_match",
        docs=[
            {"_id": 1, "g": "a", "v": 10},
            {"_id": 2, "g": "b", "v": 20},
            {"_id": 3, "g": "a", "v": 30},
        ],
        pipeline=[
            {"$match": {"g": "a"}},
            {"$group": {"_id": "$g", "total": {"$sum": "$v"}}},
        ],
        expected=[{"_id": "a", "total": 40}],
        msg="$group should only see documents that pass $match",
    ),
    StageTestCase(
        id="group_after_project",
        docs=[
            {"_id": 1, "x": 10, "y": 100},
            {"_id": 2, "x": 10, "y": 200},
        ],
        pipeline=[
            {"$project": {"x": 1}},
            {"$group": {"_id": "$x", "has_y": {"$push": "$y"}}},
        ],
        expected=[{"_id": 10, "has_y": []}],
        msg="$group should not see fields excluded by preceding $project",
    ),
    StageTestCase(
        id="group_after_addfields",
        docs=[
            {"_id": 1, "v": 5},
            {"_id": 2, "v": 15},
        ],
        pipeline=[
            {"$addFields": {"bucket": {"$cond": [{"$gte": ["$v", 10]}, "high", "low"]}}},
            {"$group": {"_id": "$bucket", "count": {"$sum": 1}}},
        ],
        expected=[
            {"_id": "high", "count": 1},
            {"_id": "low", "count": 1},
        ],
        msg="$group should see fields added by preceding $addFields",
    ),
    StageTestCase(
        id="group_after_unwind",
        docs=[
            {"_id": 1, "tags": ["a", "b"]},
            {"_id": 2, "tags": ["a", "c"]},
        ],
        pipeline=[
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        ],
        expected=[
            {"_id": "a", "count": 2},
            {"_id": "b", "count": 1},
            {"_id": "c", "count": 1},
        ],
        msg="$group should aggregate unwound documents",
    ),
    StageTestCase(
        id="group_after_sort",
        docs=[
            {"_id": 1, "g": "a", "v": 3},
            {"_id": 2, "g": "a", "v": 1},
            {"_id": 3, "g": "a", "v": 2},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$g", "first": {"$first": "$v"}, "last": {"$last": "$v"}}},
        ],
        expected=[{"_id": "a", "first": 1, "last": 3}],
        msg="$group $first/$last should respect preceding $sort order",
    ),
    StageTestCase(
        id="group_after_limit",
        docs=[{"_id": i, "v": "a"} for i in range(10)],
        pipeline=[
            {"$limit": 3},
            {"$group": {"_id": "$v", "count": {"$sum": 1}}},
        ],
        expected=[{"_id": "a", "count": 3}],
        msg="$group should only see documents that pass $limit",
    ),
    StageTestCase(
        id="group_after_skip",
        docs=[{"_id": i, "v": "a"} for i in range(10)],
        pipeline=[
            {"$skip": 7},
            {"$group": {"_id": "$v", "count": {"$sum": 1}}},
        ],
        expected=[{"_id": "a", "count": 3}],
        msg="$group should only see documents that pass $skip",
    ),
]

# Property [Post-Group Stages]: stages after $group operate on the grouped
# output documents.
GROUP_POST_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="match_after_group",
        docs=[
            {"_id": 1, "g": "a", "v": 10},
            {"_id": 2, "g": "b", "v": 20},
            {"_id": 3, "g": "a", "v": 30},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "total": {"$sum": "$v"}}},
            {"$match": {"total": {"$gte": 30}}},
        ],
        expected=[
            {"_id": "a", "total": 40},
        ],
        msg="$match after $group should filter on grouped output fields",
    ),
    StageTestCase(
        id="project_after_group",
        docs=[
            {"_id": 1, "g": "a", "v": 10},
            {"_id": 2, "g": "a", "v": 20},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "total": {"$sum": "$v"}, "count": {"$sum": 1}}},
            {"$project": {"total": 1}},
        ],
        expected=[{"_id": "a", "total": 30}],
        msg="$project after $group should reshape grouped output",
    ),
    StageTestCase(
        id="sort_after_group",
        docs=[
            {"_id": 1, "g": "b"},
            {"_id": 2, "g": "a"},
            {"_id": 3, "g": "c"},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "a", "count": 1},
            {"_id": "b", "count": 1},
            {"_id": "c", "count": 1},
        ],
        msg="$sort after $group should order grouped output",
    ),
    StageTestCase(
        id="limit_after_group",
        docs=[{"_id": i, "g": f"g{i}"} for i in range(5)],
        pipeline=[
            {"$group": {"_id": "$g", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
            {"$limit": 2},
        ],
        expected=[
            {"_id": "g0", "count": 1},
            {"_id": "g1", "count": 1},
        ],
        msg="$limit after $group should truncate grouped output",
    ),
    StageTestCase(
        id="unwind_after_group",
        docs=[
            {"_id": 1, "g": "a", "v": 10},
            {"_id": 2, "g": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$g", "vals": {"$push": "$v"}}},
            {"$unwind": "$vals"},
            {"$sort": {"vals": 1}},
        ],
        expected=[
            {"_id": "a", "vals": 10},
            {"_id": "a", "vals": 20},
        ],
        msg="$unwind after $group should expand accumulated arrays",
    ),
]

GROUP_POSITION_TESTS = GROUP_PIPELINE_POSITION_TESTS + GROUP_POST_STAGE_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_POSITION_TESTS))
def test_stages_position_group(collection, test_case: StageTestCase):
    """Test $group composing with other stages at different pipeline positions."""
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
