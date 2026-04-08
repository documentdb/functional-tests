"""Tests for $match pipeline position behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $match filters correctly regardless of its
# position in the pipeline and composes with preceding stages that reshape
# documents.
MATCH_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_first_stage",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
            {"_id": 3, "a": 10},
        ],
        pipeline=[{"$match": {"a": 10}}],
        expected=[{"_id": 1, "a": 10}, {"_id": 3, "a": 10}],
        msg="$match should work as the first stage of a pipeline",
    ),
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
        "pipeline_consecutive_match",
        docs=[
            {"_id": 1, "a": 10, "b": 1},
            {"_id": 2, "a": 20, "b": 2},
            {"_id": 3, "a": 10, "b": 3},
        ],
        pipeline=[
            {"$match": {"a": 10}},
            {"$match": {"b": 3}},
        ],
        expected=[{"_id": 3, "a": 10, "b": 3}],
        msg="$match consecutive stages should compose like $and of all predicates",
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

# Property [$text First-Stage Behavior]: $text search works inside $match when
# $match is the first stage of the pipeline.
MATCH_TEXT_FIRST_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "text_first_stage",
        docs=[
            {"_id": 1, "content": "hello world"},
            {"_id": 2, "content": "goodbye world"},
        ],
        setup=lambda collection: collection.create_index([("content", "text")]),
        pipeline=[{"$match": {"$text": {"$search": "goodbye"}}}],
        expected=[{"_id": 2, "content": "goodbye world"}],
        msg="$match with $text should work when it is the first pipeline stage",
    ),
]

MATCH_STAGE_POSITION_TESTS_ALL = MATCH_PIPELINE_POSITION_TESTS + MATCH_TEXT_FIRST_STAGE_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MATCH_STAGE_POSITION_TESTS_ALL))
def test_match_stage_position_cases(collection, test_case: StageTestCase):
    """Test $match pipeline position behavior."""
    if test_case.setup:
        test_case.setup(collection)
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
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
