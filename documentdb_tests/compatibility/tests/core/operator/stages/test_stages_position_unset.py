"""Tests for $unset composing with other stages at different pipeline positions."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $unset removes fields correctly when composed
# with other stages that filter, reshape, or aggregate documents.
UNSET_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unset_after_match",
        docs=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
        ],
        pipeline=[
            {"$match": {"a": 10}},
            {"$unset": "b"},
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$unset should remove fields from documents filtered by $match",
    ),
    StageTestCase(
        "unset_before_match",
        docs=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
        ],
        pipeline=[
            {"$unset": "b"},
            {"$match": {"a": 10}},
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$unset before $match should not affect filtering on retained fields",
    ),
    StageTestCase(
        "unset_before_match_on_removed_field",
        docs=[
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
        ],
        pipeline=[
            {"$unset": "b"},
            {"$match": {"b": 20}},
        ],
        expected=[],
        msg="$match on a field removed by a preceding $unset should return empty",
    ),
    StageTestCase(
        "unset_after_addfields",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$addFields": {"b": 20}},
            {"$unset": "a"},
        ],
        expected=[{"_id": 1, "b": 20}],
        msg="$unset should remove original fields while keeping fields added by $addFields",
    ),
    StageTestCase(
        "unset_added_field",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$addFields": {"b": 20}},
            {"$unset": "b"},
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$unset should remove a field that was added by a preceding $addFields",
    ),
    StageTestCase(
        "unset_before_addfields",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[
            {"$unset": "b"},
            {"$addFields": {"b": 99}},
        ],
        expected=[{"_id": 1, "a": 10, "b": 99}],
        msg="$addFields after $unset should re-add a removed field",
    ),
    StageTestCase(
        "unset_after_group",
        docs=[
            {"_id": 1, "cat": "a", "val": 5},
            {"_id": 2, "cat": "a", "val": 7},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
            {"$unset": "_id"},
        ],
        expected=[{"total": 12}],
        msg="$unset should remove _id from $group output",
    ),
    StageTestCase(
        "unset_after_project",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[
            {"$project": {"a": 1, "b": 1}},
            {"$unset": "b"},
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$unset should remove fields from $project output",
    ),
    StageTestCase(
        "unset_after_sort",
        docs=[
            {"_id": 1, "a": 30, "b": 1},
            {"_id": 2, "a": 10, "b": 2},
            {"_id": 3, "a": 20, "b": 3},
        ],
        pipeline=[
            {"$sort": {"a": 1}},
            {"$unset": "b"},
        ],
        expected=[
            {"_id": 2, "a": 10},
            {"_id": 3, "a": 20},
            {"_id": 1, "a": 30},
        ],
        msg="$unset should remove fields from sorted output",
    ),
    StageTestCase(
        "unset_after_unwind",
        docs=[{"_id": 1, "tags": ["x", "y"], "rm": 0}],
        pipeline=[
            {"$unwind": "$tags"},
            {"$unset": "rm"},
        ],
        expected=[
            {"_id": 1, "tags": "x"},
            {"_id": 1, "tags": "y"},
        ],
        msg="$unset should remove fields from each document produced by $unwind",
    ),
    StageTestCase(
        "unset_after_replaceroot",
        docs=[{"_id": 1, "inner": {"x": 10, "y": 20}}],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$unset": "y"},
        ],
        expected=[{"x": 10}],
        msg="$unset should remove fields from the document shape produced by $replaceRoot",
    ),
    StageTestCase(
        "unset_between_stages",
        docs=[
            {"_id": 1, "a": 10, "b": 20, "c": 30},
            {"_id": 2, "a": 40, "b": 50, "c": 60},
        ],
        pipeline=[
            {"$match": {"a": {"$gte": 10}}},
            {"$unset": "b"},
            {"$match": {"a": 10}},
        ],
        expected=[{"_id": 1, "a": 10, "c": 30}],
        msg="$unset as a middle stage should remove fields between two $match stages",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_PIPELINE_POSITION_TESTS))
def test_stage_position_unset_cases(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset composing with other stages at different pipeline positions."""
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
