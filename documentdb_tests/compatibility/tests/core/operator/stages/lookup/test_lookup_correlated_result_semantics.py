"""Tests for $lookup correlated subquery — per-document variation and result cardinality.

Covers the fundamental correlated behavior: let variable changes per outer
document, producing different join results. Also covers result array properties
(empty, single, many, ordering, $sort/$limit/$skip in sub-pipeline).
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

# Property [Correlated Subquery — Result Semantics]: the sub-pipeline re-runs
# per outer document producing independent join results; result array cardinality
# and order are controlled by sub-pipeline stages ($sort, $limit, $skip, $project).
LOOKUP_RESULT_SEMANTICS_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "per_doc_variation_distinct_let_values",
        docs=[
            {"_id": 1, "cat": "A"},
            {"_id": 2, "cat": "B"},
            {"_id": 3, "cat": "C"},
        ],
        foreign_docs=[
            {"_id": 10, "type": "A", "val": 1},
            {"_id": 11, "type": "B", "val": 2},
            {"_id": 12, "type": "B", "val": 3},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A", "val": 1}]},
            {
                "_id": 2,
                "cat": "B",
                "joined": [{"_id": 11, "type": "B", "val": 2}, {"_id": 12, "type": "B", "val": 3}],
            },
            {"_id": 3, "cat": "C", "joined": []},
        ],
        msg=(
            "$lookup correlated join should produce different results"
            " per outer document based on each doc's let var value"
        ),
    ),
    LookupTestCase(
        "per_doc_duplicate_let_values_same_result",
        docs=[
            {"_id": 1, "cat": "A"},
            {"_id": 2, "cat": "A"},
        ],
        foreign_docs=[
            {"_id": 10, "type": "A"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A"}]},
            {"_id": 2, "cat": "A", "joined": [{"_id": 10, "type": "A"}]},
        ],
        msg=(
            "$lookup correlated with duplicate let values should produce"
            " identical joined results for both outer docs"
        ),
    ),
    LookupTestCase(
        "result_empty_array_no_matches",
        docs=[{"_id": 1, "cat": "nonexistent"}],
        foreign_docs=[{"_id": 10, "type": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "cat": "nonexistent", "joined": []},
        ],
        msg="$lookup correlated with no matching foreign docs should produce empty array",
    ),
    LookupTestCase(
        "result_sort_in_sub_pipeline",
        docs=[{"_id": 1, "cat": "A"}],
        foreign_docs=[
            {"_id": 12, "type": "A", "score": 50},
            {"_id": 10, "type": "A", "score": 90},
            {"_id": 11, "type": "A", "score": 70},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$type", "$$c"]}}},
                        {"$sort": {"score": -1}},
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
                    {"_id": 10, "type": "A", "score": 90},
                    {"_id": 11, "type": "A", "score": 70},
                    {"_id": 12, "type": "A", "score": 50},
                ],
            }
        ],
        msg="$lookup sub-pipeline $sort should determine order within joined array",
    ),
    LookupTestCase(
        "result_limit_in_sub_pipeline",
        docs=[{"_id": 1, "cat": "A"}],
        foreign_docs=[
            {"_id": 10, "type": "A", "score": 90},
            {"_id": 11, "type": "A", "score": 70},
            {"_id": 12, "type": "A", "score": 50},
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
                    {"_id": 10, "type": "A", "score": 90},
                    {"_id": 11, "type": "A", "score": 70},
                ],
            }
        ],
        msg="$lookup sub-pipeline $limit should restrict joined array to N docs",
    ),
    LookupTestCase(
        "result_skip_in_sub_pipeline",
        docs=[{"_id": 1, "cat": "A"}],
        foreign_docs=[
            {"_id": 10, "type": "A", "score": 90},
            {"_id": 11, "type": "A", "score": 70},
            {"_id": 12, "type": "A", "score": 50},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$type", "$$c"]}}},
                        {"$sort": {"score": -1}},
                        {"$skip": 1},
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
                    {"_id": 11, "type": "A", "score": 70},
                    {"_id": 12, "type": "A", "score": 50},
                ],
            }
        ],
        msg="$lookup sub-pipeline $skip should skip first N joined results",
    ),
    LookupTestCase(
        "result_project_shapes_joined_docs",
        docs=[{"_id": 1, "cat": "A"}],
        foreign_docs=[
            {"_id": 10, "type": "A", "name": "Widget", "secret": "hidden"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$type", "$$c"]}}},
                        {"$project": {"name": 1, "_id": 0}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "cat": "A", "joined": [{"name": "Widget"}]},
        ],
        msg="$lookup sub-pipeline $project should reshape docs in joined array",
    ),
    LookupTestCase(
        "outer_document_order_preserved",
        docs=[
            {"_id": 3, "cat": "C"},
            {"_id": 1, "cat": "A"},
            {"_id": 2, "cat": "B"},
        ],
        foreign_docs=[
            {"_id": 10, "type": "A"},
            {"_id": 11, "type": "B"},
            {"_id": 12, "type": "C"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 3, "cat": "C", "joined": [{"_id": 12, "type": "C"}]},
            {"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A"}]},
            {"_id": 2, "cat": "B", "joined": [{"_id": 11, "type": "B"}]},
        ],
        msg="$lookup should preserve outer document order regardless of join results",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_RESULT_SEMANTICS_TESTS))
def test_lookup_correlated_result_semantics(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery per-document variation and result cardinality."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
