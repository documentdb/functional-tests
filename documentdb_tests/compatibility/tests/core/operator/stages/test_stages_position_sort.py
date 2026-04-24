"""Tests for $sort composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $sort orders documents correctly regardless of
# its position in the pipeline and composes with preceding stages that reshape
# documents.
SORT_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_first_stage",
        docs=[
            {"_id": 1, "v": 30},
            {"_id": 2, "v": 10},
            {"_id": 3, "v": 20},
        ],
        pipeline=[{"$sort": {"v": 1}}, {"$project": {"_id": 1}}],
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="$sort should work as the first stage of a pipeline",
    ),
    StageTestCase(
        "pipeline_middle_stage",
        docs=[
            {"_id": 1, "v": 30, "x": "a"},
            {"_id": 2, "v": 10, "x": "b"},
            {"_id": 3, "v": 20, "x": "c"},
        ],
        pipeline=[
            {"$match": {"v": {"$gte": 10}}},
            {"$sort": {"v": 1}},
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="$sort should work as a middle stage of a pipeline",
    ),
    StageTestCase(
        "pipeline_last_stage",
        docs=[
            {"_id": 1, "v": 30},
            {"_id": 2, "v": 10},
            {"_id": 3, "v": 20},
        ],
        pipeline=[
            {"$project": {"v": 1}},
            {"$sort": {"v": 1}},
        ],
        expected=[
            {"_id": 2, "v": 10},
            {"_id": 3, "v": 20},
            {"_id": 1, "v": 30},
        ],
        msg="$sort should work as the last stage of a pipeline",
    ),
    StageTestCase(
        "pipeline_consecutive_sort",
        docs=[
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 3, "b": 10},
        ],
        pipeline=[
            {"$sort": {"a": 1}},
            {"$sort": {"b": 1}},
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": 3}, {"_id": 2}, {"_id": 1}],
        msg="$sort consecutive stages should apply independently with last sort winning",
    ),
    StageTestCase(
        "pipeline_after_project_drops_sort_field",
        docs=[
            {"_id": 1, "v": 30, "x": "a"},
            {"_id": 2, "v": 10, "x": "b"},
            {"_id": 3, "v": 20, "x": "c"},
        ],
        pipeline=[
            {"$project": {"x": 1}},
            {"$sort": {"v": 1, "_id": 1}},
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="$sort on a field dropped by a preceding $project should treat all values as missing",
    ),
    StageTestCase(
        "pipeline_after_project_renames_field",
        docs=[
            {"_id": 1, "v": 30},
            {"_id": 2, "v": 10},
            {"_id": 3, "v": 20},
        ],
        pipeline=[
            {"$project": {"w": "$v"}},
            {"$sort": {"w": 1}},
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="$sort should sort on a field renamed by a preceding $project",
    ),
    StageTestCase(
        "pipeline_after_project_computed_field",
        docs=[
            {"_id": 1, "v": 10},
            {"_id": 2, "v": 30},
            {"_id": 3, "v": 20},
        ],
        pipeline=[
            {"$project": {"neg": {"$multiply": ["$v", -1]}}},
            {"$sort": {"neg": 1}},
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="$sort should sort on a field computed by a preceding $project",
    ),
    StageTestCase(
        "pipeline_after_group",
        docs=[
            {"_id": 1, "cat": "a", "val": 5},
            {"_id": 2, "cat": "b", "val": 3},
            {"_id": 3, "cat": "a", "val": 7},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
            {"$sort": {"total": 1}},
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": "b"}, {"_id": "a"}],
        msg="$sort should sort on fields produced by a preceding $group",
    ),
    StageTestCase(
        "pipeline_after_replaceroot",
        docs=[
            {"_id": 1, "inner": {"x": 30}},
            {"_id": 2, "inner": {"x": 10}},
            {"_id": 3, "inner": {"x": 20}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$sort": {"x": 1}},
        ],
        expected=[{"x": 10}, {"x": 20}, {"x": 30}],
        msg="$sort should sort on the document shape produced by $replaceRoot",
    ),
]

# Property [$meta Sort with Prerequisite Stages]: $sort by {$meta: 'textScore'}
# and {$meta: 'geoNearDistance'} work when preceded by the required stage.
SORT_META_PREREQUISITE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "text_score_sort_desc",
        docs=[
            {"_id": 1, "content": "apple"},
            {"_id": 2, "content": "apple apple apple"},
            {"_id": 3, "content": "banana"},
        ],
        setup=lambda collection: collection.create_index([("content", "text")]),
        pipeline=[
            {"$match": {"$text": {"$search": "apple"}}},
            {"$sort": {"score": {"$meta": "textScore"}}},
        ],
        expected=[
            {"_id": 2, "content": "apple apple apple"},
            {"_id": 1, "content": "apple"},
        ],
        msg="$sort by textScore should order documents by text search relevance",
    ),
    StageTestCase(
        "geo_near_distance_sort",
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        setup=lambda collection: collection.create_index([("loc", "2dsphere")]),
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                }
            },
            {"$sort": {"d": {"$meta": "geoNearDistance"}}},
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="$sort by geoNearDistance should order documents by distance",
    ),
]

SORT_STAGE_POSITION_TESTS_ALL = SORT_PIPELINE_POSITION_TESTS + SORT_META_PREREQUISITE_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SORT_STAGE_POSITION_TESTS_ALL))
def test_stage_position_sort_cases(collection, test_case: StageTestCase):
    """Test $sort composing with other stages at different pipeline positions."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
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
