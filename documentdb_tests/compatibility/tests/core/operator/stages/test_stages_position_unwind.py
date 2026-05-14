"""Tests for $unwind stage — pipeline integration with other stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Integration]: $unwind composes correctly with other
# aggregation stages — $match filters before/after unwind, $group aggregates
# unwound documents, $project reshapes output, $sort orders results, and
# $facet can contain $unwind branches.
UNWIND_PIPELINE_INTEGRATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_before_unwind",
        docs=[
            {"_id": 1, "status": "active", "tags": ["a", "b"]},
            {"_id": 2, "status": "inactive", "tags": ["c", "d"]},
            {"_id": 3, "status": "active", "tags": ["e"]},
        ],
        pipeline=[
            {"$match": {"status": "active"}},
            {"$unwind": {"path": "$tags"}},
        ],
        expected=[
            {"_id": 1, "status": "active", "tags": "a"},
            {"_id": 1, "status": "active", "tags": "b"},
            {"_id": 3, "status": "active", "tags": "e"},
        ],
        msg="$match before $unwind should filter documents before unwinding",
    ),
    StageTestCase(
        "match_after_unwind",
        docs=[
            {"_id": 1, "tags": ["a", "b", "c"]},
            {"_id": 2, "tags": ["b", "d"]},
        ],
        pipeline=[
            {"$unwind": {"path": "$tags"}},
            {"$match": {"tags": "b"}},
        ],
        expected=[
            {"_id": 1, "tags": "b"},
            {"_id": 2, "tags": "b"},
        ],
        msg="$match after $unwind should filter on unwound values",
    ),
    StageTestCase(
        "group_after_unwind",
        docs=[
            {"_id": 1, "items": [{"name": "x", "qty": 2}, {"name": "y", "qty": 3}]},
            {"_id": 2, "items": [{"name": "x", "qty": 5}]},
        ],
        pipeline=[
            {"$unwind": {"path": "$items"}},
            {"$group": {"_id": "$items.name", "total": {"$sum": "$items.qty"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "x", "total": 7},
            {"_id": "y", "total": 3},
        ],
        msg="$group after $unwind should aggregate across unwound documents",
    ),
    StageTestCase(
        "project_after_unwind",
        docs=[{"_id": 1, "a": [10, 20], "extra": "keep"}],
        pipeline=[
            {"$unwind": {"path": "$a"}},
            {"$project": {"val": "$a", "_id": 0}},
        ],
        expected=[
            {"val": 10},
            {"val": 20},
        ],
        msg="$project after $unwind should reshape unwound documents",
    ),
    StageTestCase(
        "sort_after_unwind",
        docs=[
            {"_id": 1, "a": [30, 10, 20]},
            {"_id": 2, "a": [5, 25]},
        ],
        pipeline=[
            {"$unwind": {"path": "$a"}},
            {"$sort": {"a": 1}},
        ],
        expected=[
            {"_id": 2, "a": 5},
            {"_id": 1, "a": 10},
            {"_id": 1, "a": 20},
            {"_id": 2, "a": 25},
            {"_id": 1, "a": 30},
        ],
        msg="$sort after $unwind should order unwound documents",
    ),
    StageTestCase(
        "unwind_in_facet",
        docs=[
            {"_id": 1, "tags": ["a", "b"], "scores": [10, 20]},
            {"_id": 2, "tags": ["c"], "scores": [30]},
        ],
        pipeline=[
            {
                "$facet": {
                    "by_tag": [
                        {"$unwind": {"path": "$tags"}},
                        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                        {"$sort": {"_id": 1}},
                    ],
                    "by_score": [
                        {"$unwind": {"path": "$scores"}},
                        {"$group": {"_id": None, "avg": {"$avg": "$scores"}}},
                    ],
                }
            }
        ],
        expected=[
            {
                "by_tag": [
                    {"_id": "a", "count": 1},
                    {"_id": "b", "count": 1},
                    {"_id": "c", "count": 1},
                ],
                "by_score": [
                    {"_id": None, "avg": 20.0},
                ],
            }
        ],
        msg="$unwind inside $facet branches should operate independently",
    ),
    StageTestCase(
        "addfields_after_unwind",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[
            {"$unwind": {"path": "$a", "includeArrayIndex": "idx"}},
            {"$addFields": {"label": {"$concat": ["item_", {"$toString": "$idx"}]}}},
            {"$project": {"a": 1, "label": 1}},
        ],
        expected=[
            {"_id": 1, "a": 10, "label": "item_0"},
            {"_id": 1, "a": 20, "label": "item_1"},
        ],
        msg="$addFields after $unwind should be able to reference includeArrayIndex field",
    ),
    StageTestCase(
        "unwind_then_group_count",
        docs=[
            {"_id": 1, "tags": ["a", "b", "a"]},
            {"_id": 2, "tags": ["b", "c"]},
            {"_id": 3, "tags": ["a"]},
        ],
        pipeline=[
            {"$unwind": {"path": "$tags"}},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "a", "count": 3},
            {"_id": "b", "count": 2},
            {"_id": "c", "count": 1},
        ],
        msg="$unwind + $group should correctly count occurrences including duplicates",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_PIPELINE_INTEGRATION_TESTS))
def test_unwind_pipeline_integration(collection, test_case: StageTestCase):
    """Test $unwind pipeline integration with other stages."""
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
