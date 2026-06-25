"""Tests for $redact composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $redact composes correctly with preceding stages
# that reshape documents and with following stages that consume its output.
REDACT_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_after_computed_field",
        docs=[{"_id": 1, "level": 2}, {"_id": 2, "level": 8}],
        pipeline=[
            {"$set": {"allowed": {"$lt": ["$level", 5]}}},
            {"$redact": {"$cond": [{"$eq": ["$allowed", True]}, "$$KEEP", "$$PRUNE"]}},
        ],
        expected=[{"_id": 1, "level": 2, "allowed": True}],
        msg="$redact should evaluate its condition against a field computed by a preceding stage",
    ),
    StageTestCase(
        "pipeline_before_match_on_pruned_field",
        docs=[
            {"_id": 1, "detail": {"restricted": False, "flag": True}},
            {"_id": 2, "detail": {"restricted": True, "flag": True}},
        ],
        pipeline=[
            {"$redact": {"$cond": [{"$eq": ["$restricted", True]}, "$$PRUNE", "$$DESCEND"]}},
            {"$match": {"detail.flag": True}},
        ],
        expected=[{"_id": 1, "detail": {"restricted": False, "flag": True}}],
        msg="a following $match should filter on the redacted output, excluding a document "
        "whose matchable field $redact pruned while keeping one whose field survived",
    ),
    StageTestCase(
        "pipeline_before_count_of_survivors",
        docs=[
            {"_id": 1, "status": "public"},
            {"_id": 2, "status": "secret"},
            {"_id": 3, "status": "public"},
        ],
        pipeline=[
            {"$redact": {"$cond": [{"$eq": ["$status", "public"]}, "$$KEEP", "$$PRUNE"]}},
            {"$count": "n"},
        ],
        expected=[{"n": 2}],
        msg="a following $count should count only the documents $redact kept",
    ),
    StageTestCase(
        "pipeline_middle_stage",
        docs=[
            {"_id": 1, "status": "public", "a": 1},
            {"_id": 2, "status": "secret", "a": 3},
            {"_id": 3, "status": "public", "a": 5},
        ],
        pipeline=[
            {"$match": {"a": {"$gt": 0}}},
            {"$redact": {"$cond": [{"$eq": ["$status", "public"]}, "$$KEEP", "$$PRUNE"]}},
            {"$project": {"a": 1}},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 5}],
        msg="$redact should work as a middle stage between a preceding and a following stage",
    ),
    StageTestCase(
        "pipeline_last_stage",
        docs=[
            {"_id": 1, "status": "public", "a": 1},
            {"_id": 2, "status": "secret", "a": 2},
        ],
        pipeline=[
            {"$project": {"status": 1, "a": 1}},
            {"$redact": {"$cond": [{"$eq": ["$status", "public"]}, "$$KEEP", "$$PRUNE"]}},
        ],
        expected=[{"_id": 1, "status": "public", "a": 1}],
        msg="$redact should work as the last stage of a pipeline",
    ),
    StageTestCase(
        "pipeline_after_unwind",
        docs=[{"_id": 1, "items": [{"status": "public", "v": 1}, {"status": "secret", "v": 2}]}],
        pipeline=[
            {"$unwind": "$items"},
            {"$redact": {"$cond": [{"$eq": ["$items.status", "public"]}, "$$KEEP", "$$PRUNE"]}},
        ],
        expected=[{"_id": 1, "items": {"status": "public", "v": 1}}],
        msg="$redact should evaluate each document produced by a preceding $unwind independently",
    ),
    StageTestCase(
        "pipeline_after_root_replacement",
        docs=[
            {"_id": 1, "inner": {"status": "public", "x": 1}},
            {"_id": 2, "inner": {"status": "secret", "x": 2}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$redact": {"$cond": [{"$eq": ["$status", "public"]}, "$$KEEP", "$$PRUNE"]}},
        ],
        expected=[{"status": "public", "x": 1}],
        msg="$redact should evaluate its condition against the shape produced by a "
        "root replacement stage",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REDACT_PIPELINE_POSITION_TESTS))
def test_stage_position_redact_cases(collection, test_case: StageTestCase):
    """Test $redact composing with other stages at different pipeline positions."""
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
