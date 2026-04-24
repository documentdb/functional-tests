"""Tests for $set composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $set adds or overwrites fields correctly when
# composed with other stage types at different pipeline positions.
SET_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_after_match",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 30},
        ],
        pipeline=[
            {"$match": {"a": {"$gt": 15}}},
            {"$set": {"b": {"$multiply": ["$a", 2]}}},
        ],
        expected=[{"_id": 2, "a": 30, "b": 60}],
        msg="$set should work after a $match stage",
    ),
    StageTestCase(
        "pipeline_before_match",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 30},
        ],
        pipeline=[
            {"$set": {"b": {"$multiply": ["$a", 2]}}},
            {"$match": {"b": {"$gt": 40}}},
        ],
        expected=[{"_id": 2, "a": 30, "b": 60}],
        msg="$set should add fields visible to a subsequent $match stage",
    ),
    StageTestCase(
        "pipeline_set_then_sort",
        docs=[
            {"_id": 1, "a": 30},
            {"_id": 2, "a": 10},
            {"_id": 3, "a": 20},
        ],
        pipeline=[
            {"$set": {"b": {"$multiply": ["$a", -1]}}},
            {"$sort": {"b": 1}},
        ],
        expected=[
            {"_id": 1, "a": 30, "b": -30},
            {"_id": 3, "a": 20, "b": -20},
            {"_id": 2, "a": 10, "b": -10},
        ],
        msg="$set should add fields usable by a subsequent $sort stage",
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
            {"$set": {"doubled": {"$multiply": ["$total", 2]}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "a", "total": 12, "doubled": 24},
            {"_id": "b", "total": 3, "doubled": 6},
        ],
        msg="$set should compute fields from $group output",
    ),
    StageTestCase(
        "pipeline_before_group",
        docs=[
            {"_id": 1, "cat": "a", "val": 5},
            {"_id": 2, "cat": "a", "val": 7},
        ],
        pipeline=[
            {"$set": {"doubled": {"$multiply": ["$val", 2]}}},
            {"$group": {"_id": "$cat", "total": {"$sum": "$doubled"}}},
        ],
        expected=[{"_id": "a", "total": 24}],
        msg="$set should add fields usable by a subsequent $group stage",
    ),
    StageTestCase(
        "pipeline_after_unwind",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[
            {"$unwind": "$a"},
            {"$set": {"b": {"$multiply": ["$a", 2]}}},
        ],
        expected=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 1, "a": 20, "b": 40},
        ],
        msg="$set should add fields to each unwound document",
    ),
    StageTestCase(
        "pipeline_after_project",
        docs=[{"_id": 1, "a": 5, "b": 10}],
        pipeline=[
            {"$project": {"a": 1}},
            {"$set": {"c": {"$multiply": ["$a", 3]}}},
        ],
        expected=[{"_id": 1, "a": 5, "c": 15}],
        msg="$set should add fields to documents narrowed by $project",
    ),
    StageTestCase(
        "pipeline_after_replaceRoot",
        docs=[{"_id": 1, "inner": {"x": 10, "y": 20}}],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$set": {"z": {"$add": ["$x", "$y"]}}},
        ],
        expected=[{"x": 10, "y": 20, "z": 30}],
        msg="$set should add fields to documents produced by $replaceRoot",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SET_PIPELINE_POSITION_TESTS))
def test_stages_position_set_cases(collection, test_case: StageTestCase):
    """Test $set composing with other stages at different pipeline positions."""
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
