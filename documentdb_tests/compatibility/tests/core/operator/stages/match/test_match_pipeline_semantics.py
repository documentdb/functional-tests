"""Tests for $match pipeline semantics."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Semantics]: $match works as a standalone pipeline
# participant and composes correctly with other $match stages.
MATCH_PIPELINE_SEMANTICS_TESTS: list[StageTestCase] = [
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
        msg="$match consecutive stages should compose like AND of all predicates",
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

MATCH_PIPELINE_SEMANTICS_TESTS_ALL = MATCH_PIPELINE_SEMANTICS_TESTS + MATCH_TEXT_FIRST_STAGE_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MATCH_PIPELINE_SEMANTICS_TESTS_ALL))
def test_match_pipeline_semantics_cases(collection, test_case: StageTestCase):
    """Test $match pipeline semantics."""
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
        ignore_doc_order=True,
    )
