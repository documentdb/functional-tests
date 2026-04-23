"""Tests for $project composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $project reshapes documents correctly when
# composed with other stage types at different pipeline positions.
PROJECT_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_after_match",
        docs=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
        ],
        pipeline=[
            {"$match": {"a": {"$gt": 15}}},
            {"$project": {"b": 1}},
        ],
        expected=[{"_id": 2, "b": 40}],
        msg="$project should work after a $match stage",
    ),
    StageTestCase(
        "pipeline_before_match",
        docs=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
        ],
        pipeline=[
            {"$project": {"a": 1}},
            {"$match": {"a": {"$gt": 15}}},
        ],
        expected=[{"_id": 2, "a": 30}],
        msg="$project should work before a $match stage",
    ),
    StageTestCase(
        "pipeline_project_then_sort",
        docs=[
            {"_id": 1, "a": 30, "b": 1},
            {"_id": 2, "a": 10, "b": 2},
            {"_id": 3, "a": 20, "b": 3},
        ],
        pipeline=[
            {"$project": {"a": 1}},
            {"$sort": {"a": 1}},
        ],
        expected=[
            {"_id": 2, "a": 10},
            {"_id": 3, "a": 20},
            {"_id": 1, "a": 30},
        ],
        msg="$project should compose with a subsequent $sort stage",
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
            {"$project": {"total": 1}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "a", "total": 12},
            {"_id": "b", "total": 3},
        ],
        msg="$project should reshape documents produced by $group",
    ),
    StageTestCase(
        "pipeline_before_group",
        docs=[
            {"_id": 1, "cat": "a", "val": 5, "extra": "x"},
            {"_id": 2, "cat": "a", "val": 7, "extra": "y"},
        ],
        pipeline=[
            {"$project": {"cat": 1, "val": 1}},
            {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
        ],
        expected=[{"_id": "a", "total": 12}],
        msg="$project should narrow fields before $group",
    ),
    StageTestCase(
        "pipeline_after_unwind",
        docs=[{"_id": 1, "a": [10, 20], "b": "keep"}],
        pipeline=[
            {"$unwind": "$a"},
            {"$project": {"a": 1}},
        ],
        expected=[
            {"_id": 1, "a": 10},
            {"_id": 1, "a": 20},
        ],
        msg="$project should reshape unwound documents",
    ),
    StageTestCase(
        "pipeline_after_addFields",
        docs=[{"_id": 1, "a": 5}],
        pipeline=[
            {"$addFields": {"b": {"$multiply": ["$a", 2]}}},
            {"$project": {"b": 1}},
        ],
        expected=[{"_id": 1, "b": 10}],
        msg="$project should include fields added by $addFields",
    ),
    StageTestCase(
        "pipeline_after_replaceRoot",
        docs=[{"_id": 1, "inner": {"x": 10, "y": 20}}],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$project": {"x": 1}},
        ],
        expected=[{"x": 10}],
        msg="$project should reshape documents after $replaceRoot",
    ),
    StageTestCase(
        "pipeline_project_meta_textscore",
        docs=[
            {"_id": 1, "content": "apple"},
            {"_id": 2, "content": "banana"},
        ],
        setup=lambda collection: collection.create_index([("content", "text")]),
        pipeline=[
            {"$match": {"$text": {"$search": "apple"}}},
            {"$project": {"_id": 1, "score": {"$meta": "textScore"}}},
            {"$match": {"score": {"$gt": 0}}},
            {"$project": {"_id": 1}},
        ],
        expected=[
            {"_id": 1},
        ],
        msg=(
            "$project with $meta textScore should produce a"
            " positive score field for matching documents"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(PROJECT_PIPELINE_POSITION_TESTS))
def test_stages_position_project_cases(collection, test_case: StageTestCase):
    """Test $project composing with other stages at different pipeline positions."""
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
