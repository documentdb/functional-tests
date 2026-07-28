"""Tests for let variable access across multi-stage $lookup sub-pipelines.

Verifies a let variable stays accessible when other aggregation stages sit
between the let binding and the stage that uses it, and when several let
variables are used across a sequence of stages.
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

# Property [Stage Combination Let Access]: let variables remain accessible
# across a multi-stage sub-pipeline, both before and after intervening stages.
LOOKUP_VERBOSE_STAGE_COMBINATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_var_after_unwind",
        foreign_docs=[{"_id": 10, "items": [{"type": "A", "v": 1}, {"type": "B", "v": 2}]}],
        docs=[{"_id": 1, "wantType": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "wantType": "A",
                "joined": [{"_id": 10, "items": {"type": "A", "v": 1}}],
            }
        ],
        msg="$lookup let var should be accessible in $match after $unwind in the sub-pipeline",
    ),
    LookupTestCase(
        "let_var_after_group",
        foreign_docs=[
            {"_id": 10, "cat": "A", "amount": 60},
            {"_id": 11, "cat": "A", "amount": 50},
            {"_id": 12, "cat": "B", "amount": 30},
        ],
        docs=[{"_id": 1, "minTotal": 100}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"min": "$minTotal"},
                    "pipeline": [
                        {"$group": {"_id": "$cat", "total": {"$sum": "$amount"}}},
                        {"$match": {"$expr": {"$gte": ["$total", "$$min"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "minTotal": 100, "joined": [{"_id": "A", "total": 110}]}],
        msg="$lookup let var should be accessible in $match after $group in the sub-pipeline",
    ),
    LookupTestCase(
        "let_var_before_and_after_group",
        foreign_docs=[
            {"_id": 10, "type": "A", "amount": 5},
            {"_id": 11, "type": "A", "amount": 7},
            {"_id": 12, "type": "B", "amount": 9},
        ],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": "A", "total": 12, "whichCat": "A"}]}],
        msg="$lookup should keep a let var accessible both in a $match before a "
        "$group and in an $addFields after it",
    ),
    LookupTestCase(
        "let_var_in_addFields_then_sort",
        foreign_docs=[
            {"_id": 10, "score": 60},
            {"_id": 11, "score": 80},
            {"_id": 12, "score": 75},
        ],
        docs=[{"_id": 1, "target": 70}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "target": 70,
                "joined": [
                    {"_id": 12, "score": 75, "diff": 5},
                    {"_id": 10, "score": 60, "diff": 10},
                    {"_id": 11, "score": 80, "diff": 10},
                ],
            }
        ],
        msg="$lookup let var in $addFields should feed a following $sort by "
        "proximity to the target",
    ),
    LookupTestCase(
        "let_var_top_n_pattern",
        foreign_docs=[
            {"_id": 10, "type": "A", "score": 50},
            {"_id": 11, "type": "A", "score": 90},
            {"_id": 12, "type": "A", "score": 70},
            {"_id": 13, "type": "B", "score": 95},
        ],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$type", "$$c"]}}},
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
                "cat": "A",
                "joined": [
                    {"_id": 11, "type": "A", "score": 90},
                    {"_id": 12, "type": "A", "score": 70},
                ],
            }
        ],
        msg="$lookup top-N pattern with a let var $match then $sort and $limit "
        "should return the top matches",
    ),
    LookupTestCase(
        "let_var_reused_in_multiple_stages",
        foreign_docs=[{"_id": 10, "score": 80}, {"_id": 11, "score": 30}],
        docs=[{"_id": 1, "threshold": 50}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
            {"_id": 1, "threshold": 50, "joined": [{"_id": 10, "score": 80, "above_by": 30}]}
        ],
        msg="$lookup should keep the same let var accessible in both $match and a later $addFields",
    ),
    LookupTestCase(
        "three_different_let_vars_in_sequence",
        foreign_docs=[{"_id": 10, "score": 80}, {"_id": 11, "score": 30}],
        docs=[{"_id": 1, "minScore": 50, "label": "high", "multiplier": 2}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "minScore": 50,
                "label": "high",
                "multiplier": 2,
                "joined": [{"_id": 10, "score": 80, "tag": "high", "scaled": 160}],
            }
        ],
        msg="$lookup should access three different let vars used across sequential "
        "sub-pipeline stages",
    ),
    LookupTestCase(
        "let_var_after_project",
        foreign_docs=[{"_id": 10, "name": "task", "extra": "ignored"}],
        docs=[{"_id": 1, "suffix": "_done"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"sfx": "$suffix"},
                    "pipeline": [
                        {"$project": {"name": 1, "_id": 0}},
                        {"$addFields": {"full": {"$concat": ["$name", "$$sfx"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "suffix": "_done", "joined": [{"name": "task", "full": "task_done"}]}],
        msg="$lookup let var should be accessible in $addFields after $project in the sub-pipeline",
    ),
    LookupTestCase(
        "let_var_after_replace_root",
        foreign_docs=[{"_id": 10, "score": 80}],
        docs=[{"_id": 1, "tag": "kept"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"t": "$tag"},
                    "pipeline": [
                        {"$replaceRoot": {"newRoot": {"score": "$score"}}},
                        {"$addFields": {"lv": "$$t"}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "tag": "kept", "joined": [{"score": 80, "lv": "kept"}]}],
        msg="$lookup let var should remain accessible in $addFields after "
        "$replaceRoot swaps the document root",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_VERBOSE_STAGE_COMBINATION_TESTS))
def test_verbose_stage_combinations(collection, test_case: LookupTestCase):
    """Test let variable access across multi-stage $lookup sub-pipelines."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
