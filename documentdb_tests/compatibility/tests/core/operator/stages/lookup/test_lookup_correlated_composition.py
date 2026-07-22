"""Tests for $lookup correlated subquery — sub-pipeline composition with other stages.

Verifies let variables remain accessible when the sub-pipeline contains
various aggregation stages in sequence ($unwind, $group, $sort, $limit, $facet).
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

# Property [Correlated Subquery — Stage Composition]: let variables remain
# accessible when the sub-pipeline contains other aggregation stages between
# the let binding and the $match or $addFields usage.
LOOKUP_COMPOSITION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_var_after_unwind",
        docs=[{"_id": 1, "wantType": "A"}],
        foreign_docs=[
            {"_id": 10, "items": [{"type": "A", "v": 1}, {"type": "B", "v": 2}]},
        ],
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
        msg="$lookup let var should be accessible in $match after $unwind in sub-pipeline",
    ),
    LookupTestCase(
        "let_var_after_group",
        docs=[{"_id": 1, "minTotal": 100}],
        foreign_docs=[
            {"_id": 10, "cat": "A", "amount": 60},
            {"_id": 11, "cat": "A", "amount": 50},
            {"_id": 12, "cat": "B", "amount": 30},
        ],
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
        expected=[
            {
                "_id": 1,
                "minTotal": 100,
                "joined": [{"_id": "A", "total": 110}],
            }
        ],
        msg="$lookup let var should be accessible in $match after $group in sub-pipeline",
    ),
    LookupTestCase(
        "let_var_in_addFields_then_sort",
        docs=[{"_id": 1, "target": 70}],
        foreign_docs=[
            {"_id": 10, "score": 60},
            {"_id": 11, "score": 80},
            {"_id": 12, "score": 75},
        ],
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
        msg=(
            "$lookup let var in $addFields producing diff then $sort"
            " should order by proximity to let var target"
        ),
    ),
    LookupTestCase(
        "let_var_top_n_pattern",
        docs=[{"_id": 1, "cat": "A"}],
        foreign_docs=[
            {"_id": 10, "type": "A", "score": 50},
            {"_id": 11, "type": "A", "score": 90},
            {"_id": 12, "type": "A", "score": 70},
            {"_id": 13, "type": "B", "score": 95},
        ],
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
        msg=(
            "$lookup correlated top-N pattern: $match with let var,"
            " $sort, $limit should return top N matching docs"
        ),
    ),
    LookupTestCase(
        "let_var_reused_in_multiple_stages",
        docs=[{"_id": 1, "threshold": 50}],
        foreign_docs=[
            {"_id": 10, "score": 80},
            {"_id": 11, "score": 30},
        ],
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
            {
                "_id": 1,
                "threshold": 50,
                "joined": [{"_id": 10, "score": 80, "above_by": 30}],
            }
        ],
        msg=(
            "$lookup same let var used in $match and $addFields should"
            " be accessible in both stages"
        ),
    ),
    LookupTestCase(
        "three_different_let_vars_in_sequence",
        docs=[{"_id": 1, "minScore": 50, "label": "high", "multiplier": 2}],
        foreign_docs=[
            {"_id": 10, "score": 80},
            {"_id": 11, "score": 30},
        ],
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
        msg=(
            "$lookup pipeline using 3 different let vars in sequential"
            " stages should access all correctly"
        ),
    ),
    LookupTestCase(
        "let_var_after_project",
        docs=[{"_id": 1, "suffix": "_done"}],
        foreign_docs=[{"_id": 10, "name": "task", "extra": "ignored"}],
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
        expected=[
            {
                "_id": 1,
                "suffix": "_done",
                "joined": [{"name": "task", "full": "task_done"}],
            }
        ],
        msg="$lookup let var should be accessible in $addFields after $project in sub-pipeline",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_COMPOSITION_TESTS))
def test_lookup_correlated_composition(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery sub-pipeline composition with other stages."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
