"""Tests for $match composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $match filters correctly when composed with
# preceding stages that reshape documents.
MATCH_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_middle_stage",
        docs=[
            {"_id": 1, "a": 10, "b": "x"},
            {"_id": 2, "a": 20, "b": "y"},
            {"_id": 3, "a": 10, "b": "z"},
        ],
        pipeline=[
            {"$project": {"a": 1}},
            {"$match": {"a": 10}},
            {"$project": {"a": 1}},
        ],
        expected=[{"_id": 1, "a": 10}, {"_id": 3, "a": 10}],
        msg="$match should work as a middle stage of a pipeline",
    ),
    StageTestCase(
        "pipeline_last_stage",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
            {"_id": 3, "a": 10},
        ],
        pipeline=[
            {"$project": {"a": 1}},
            {"$match": {"a": 10}},
        ],
        expected=[{"_id": 1, "a": 10}, {"_id": 3, "a": 10}],
        msg="$match should work as the last stage of a pipeline",
    ),
    StageTestCase(
        "pipeline_after_reshape_dropped_field",
        docs=[
            {"_id": 1, "a": 10, "b": "x"},
            {"_id": 2, "a": 20, "b": "y"},
        ],
        pipeline=[
            {"$project": {"b": 1}},
            {"$match": {"a": 10}},
        ],
        expected=[],
        msg="$match on a field dropped by a preceding stage should return empty",
    ),
    StageTestCase(
        "pipeline_after_reshape_computed_field",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
        ],
        pipeline=[
            {"$project": {"doubled": {"$multiply": ["$a", 2]}}},
            {"$match": {"doubled": 40}},
        ],
        expected=[{"_id": 2, "doubled": 40}],
        msg="$match should filter on fields computed by a preceding stage",
    ),
    StageTestCase(
        "pipeline_after_aggregation_computed_field",
        docs=[
            {"_id": 1, "cat": "a", "val": 5},
            {"_id": 2, "cat": "b", "val": 3},
            {"_id": 3, "cat": "a", "val": 7},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
            {"$match": {"total": 12}},
        ],
        expected=[{"_id": "a", "total": 12}],
        msg="$match should filter on fields produced by an aggregation stage",
    ),
    StageTestCase(
        "pipeline_after_aggregation_dropped_field",
        docs=[
            {"_id": 1, "cat": "a", "val": 5},
            {"_id": 2, "cat": "b", "val": 3},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
            {"$match": {"val": 5}},
        ],
        expected=[],
        msg="$match on a field absent from aggregation output should return empty",
    ),
    StageTestCase(
        "pipeline_after_root_replacement",
        docs=[
            {"_id": 1, "inner": {"x": 10}},
            {"_id": 2, "inner": {"x": 20}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$match": {"x": 10}},
        ],
        expected=[{"x": 10}],
        msg="$match should filter on the document shape produced by a root replacement stage",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MATCH_PIPELINE_POSITION_TESTS))
def test_stage_position_match_cases(collection, test_case: StageTestCase):
    """Test $match composing with other stages at different pipeline positions."""
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
