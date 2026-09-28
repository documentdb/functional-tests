"""Tests for let variable access across multi-stage $lookup concise sub-pipelines.

Verifies that let variables remain accessible when the concise syntax equality
prefilter is combined with a multi-stage pipeline, and that the equality match
correctly narrows the set before the pipeline stages execute.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Concise Stage Combination]: let variables remain accessible across
# a multi-stage sub-pipeline when combined with concise equality prefilter.
LOOKUP_CONCISE_STAGE_COMBINATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "equality_then_unwind_then_let_match",
        foreign_docs=[
            {"_id": 10, "ff": "a", "items": [{"type": "X", "v": 1}, {"type": "Y", "v": 2}]},
            {"_id": 11, "ff": "a", "items": [{"type": "X", "v": 3}]},
            {"_id": 12, "ff": "b", "items": [{"type": "X", "v": 4}]},
        ],
        docs=[{"_id": 1, "lf": "a", "wantType": "X"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"t": "$wantType"},
                    "pipeline": [
                        {"$unwind": "$items"},
                        {"$match": {"$expr": {"$eq": ["$items.type", "$$t"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "wantType": "X",
                "joined": [
                    {"_id": 10, "ff": "a", "items": {"type": "X", "v": 1}},
                    {"_id": 11, "ff": "a", "items": {"type": "X", "v": 3}},
                ],
            }
        ],
        msg="$lookup concise should apply equality first, then let var should be "
        "accessible in $match after $unwind",
    ),
    LookupTestCase(
        "equality_then_group_then_let_filter",
        foreign_docs=[
            {"_id": 10, "ff": "a", "cat": "X", "amount": 60},
            {"_id": 11, "ff": "a", "cat": "X", "amount": 50},
            {"_id": 12, "ff": "a", "cat": "Y", "amount": 30},
            {"_id": 13, "ff": "b", "cat": "X", "amount": 200},
        ],
        docs=[{"_id": 1, "lf": "a", "minTotal": 100}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"min": "$minTotal"},
                    "pipeline": [
                        {"$group": {"_id": "$cat", "total": {"$sum": "$amount"}}},
                        {"$match": {"$expr": {"$gte": ["$total", "$$min"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "minTotal": 100, "joined": [{"_id": "X", "total": 110}]}],
        msg="$lookup concise should apply equality first (excluding ff=b), then "
        "let var should be accessible in $match after $group",
    ),
    LookupTestCase(
        "equality_then_sort_limit_top_n",
        foreign_docs=[
            {"_id": 10, "ff": "a", "score": 50},
            {"_id": 11, "ff": "a", "score": 90},
            {"_id": 12, "ff": "a", "score": 70},
            {"_id": 13, "ff": "b", "score": 95},
        ],
        docs=[{"_id": 1, "lf": "a", "minScore": 60}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"min": "$minScore"},
                    "pipeline": [
                        {"$match": {"$expr": {"$gte": ["$score", "$$min"]}}},
                        {"$sort": {"score": -1}},
                        {"$limit": 2},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "minScore": 60,
                "joined": [
                    {"_id": 11, "ff": "a", "score": 90},
                    {"_id": 12, "ff": "a", "score": 70},
                ],
            }
        ],
        msg="$lookup concise top-N pattern: equality prefilter, let var $match, "
        "$sort, $limit should return top matches from the equality subset",
    ),
    LookupTestCase(
        "equality_then_addFields_using_let",
        foreign_docs=[
            {"_id": 10, "ff": "a", "score": 80},
            {"_id": 11, "ff": "a", "score": 60},
            {"_id": 12, "ff": "b", "score": 90},
        ],
        docs=[{"_id": 1, "lf": "a", "target": 70}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"tgt": "$target"},
                    "pipeline": [
                        {"$addFields": {"diff": {"$abs": {"$subtract": ["$score", "$$tgt"]}}}},
                        {"$sort": {"diff": 1, "_id": 1}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "target": 70,
                "joined": [
                    {"_id": 10, "ff": "a", "score": 80, "diff": 10},
                    {"_id": 11, "ff": "a", "score": 60, "diff": 10},
                ],
            }
        ],
        msg="$lookup concise should apply equality first, then let var in "
        "$addFields should feed a following $sort",
    ),
    LookupTestCase(
        "equality_then_project_then_let_addFields",
        foreign_docs=[
            {"_id": 10, "ff": "a", "name": "task1", "extra": "ignored"},
            {"_id": 11, "ff": "b", "name": "task2", "extra": "also_ignored"},
        ],
        docs=[{"_id": 1, "lf": "a", "suffix": "_done"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"sfx": "$suffix"},
                    "pipeline": [
                        {"$project": {"name": 1, "_id": 0}},
                        {"$addFields": {"full": {"$concat": ["$name", "$$sfx"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "suffix": "_done",
                "joined": [{"name": "task1", "full": "task1_done"}],
            }
        ],
        msg="$lookup concise should apply equality first, then let var should be "
        "accessible in $addFields after $project",
    ),
    LookupTestCase(
        "equality_then_replaceRoot_then_let_addFields",
        foreign_docs=[
            {"_id": 10, "ff": "a", "data": {"score": 80}},
            {"_id": 11, "ff": "b", "data": {"score": 90}},
        ],
        docs=[{"_id": 1, "lf": "a", "tag": "kept"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"t": "$tag"},
                    "pipeline": [
                        {"$replaceRoot": {"newRoot": "$data"}},
                        {"$addFields": {"lv": "$$t"}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "tag": "kept", "joined": [{"score": 80, "lv": "kept"}]}],
        msg="$lookup concise should apply equality first, then let var should remain "
        "accessible after $replaceRoot swaps the document root",
    ),
    LookupTestCase(
        "equality_then_let_before_and_after_group",
        foreign_docs=[
            {"_id": 10, "ff": "a", "type": "X", "amount": 5},
            {"_id": 11, "ff": "a", "type": "X", "amount": 7},
            {"_id": 12, "ff": "a", "type": "Y", "amount": 9},
            {"_id": 13, "ff": "b", "type": "X", "amount": 100},
        ],
        docs=[{"_id": 1, "lf": "a", "cat": "X"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"c": "$cat"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$type", "$$c"]}}},
                        {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}},
                        {"$addFields": {"whichCat": "$$c"}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "cat": "X",
                "joined": [{"_id": "X", "total": 12, "whichCat": "X"}],
            }
        ],
        msg="$lookup concise should keep a let var accessible both in a $match "
        "before a $group and in an $addFields after it",
    ),
    LookupTestCase(
        "equality_then_let_reused_in_multiple_stages",
        foreign_docs=[
            {"_id": 10, "ff": "a", "score": 80},
            {"_id": 11, "ff": "a", "score": 30},
            {"_id": 12, "ff": "b", "score": 90},
        ],
        docs=[{"_id": 1, "lf": "a", "threshold": 50}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"thr": "$threshold"},
                    "pipeline": [
                        {"$match": {"$expr": {"$gte": ["$score", "$$thr"]}}},
                        {"$addFields": {"above_by": {"$subtract": ["$score", "$$thr"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "threshold": 50,
                "joined": [{"_id": 10, "ff": "a", "score": 80, "above_by": 30}],
            }
        ],
        msg="$lookup concise should keep the same let var accessible in both "
        "$match and a later $addFields",
    ),
    LookupTestCase(
        "equality_then_three_different_let_vars_in_sequence",
        foreign_docs=[
            {"_id": 10, "ff": "a", "score": 80},
            {"_id": 11, "ff": "a", "score": 30},
            {"_id": 12, "ff": "b", "score": 90},
        ],
        docs=[{"_id": 1, "lf": "a", "minScore": 50, "label": "high", "multiplier": 2}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"min": "$minScore", "lbl": "$label", "mult": "$multiplier"},
                    "pipeline": [
                        {"$match": {"$expr": {"$gte": ["$score", "$$min"]}}},
                        {"$addFields": {"tag": "$$lbl"}},
                        {"$addFields": {"scaled": {"$multiply": ["$score", "$$mult"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "minScore": 50,
                "label": "high",
                "multiplier": 2,
                "joined": [{"_id": 10, "ff": "a", "score": 80, "tag": "high", "scaled": 160}],
            }
        ],
        msg="$lookup concise should access three different let vars used across "
        "sequential sub-pipeline stages",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CONCISE_STAGE_COMBINATION_TESTS))
def test_lookup_concise_stage_combinations(collection, test_case: LookupTestCase):
    """Test let variable access across multi-stage $lookup concise sub-pipelines."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
