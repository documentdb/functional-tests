"""Tests for $lookup composing with other stages at different pipeline positions."""

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

# Property [Pipeline Position]: $lookup produces correct results when
# composed with other stage types at different pipeline positions.
LOOKUP_PIPELINE_POSITION_TESTS: list[LookupTestCase] = [
    # Stages before $lookup.
    LookupTestCase(
        "match_before_lookup_filters_input",
        docs=[
            {"_id": 1, "lf": "a", "val": 10},
            {"_id": 2, "lf": "b", "val": 20},
        ],
        foreign_docs=[{"_id": 10, "ff": "b"}],
        pipeline=[
            {"$match": {"val": {"$gte": 20}}},
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
        ],
        expected=[
            {"_id": 2, "lf": "b", "val": 20, "j": [{"_id": 10, "ff": "b"}]},
        ],
        msg="$match before $lookup should filter input documents",
    ),
    LookupTestCase(
        "sort_before_lookup_preserves_order",
        docs=[
            {"_id": 1, "lf": "a", "val": 10},
            {"_id": 2, "lf": "a", "val": 30},
        ],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {"$sort": {"val": -1}},
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$project": {"val": 1}},
        ],
        expected=[
            {"_id": 2, "val": 30},
            {"_id": 1, "val": 10},
        ],
        msg="$sort before $lookup should preserve document order",
    ),
    LookupTestCase(
        "limit_before_lookup",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "a"},
            {"_id": 3, "lf": "a"},
        ],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$limit": 2},
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$project": {"j_count": {"$size": "$j"}}},
        ],
        expected=[
            {"_id": 1, "j_count": 1},
            {"_id": 2, "j_count": 1},
        ],
        msg="$limit before $lookup should restrict input documents",
    ),
    LookupTestCase(
        "skip_before_lookup",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "a"},
            {"_id": 3, "lf": "a"},
        ],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$skip": 2},
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$project": {"j_count": {"$size": "$j"}}},
        ],
        expected=[{"_id": 3, "j_count": 1}],
        msg="$skip before $lookup should skip input documents",
    ),
    LookupTestCase(
        "project_before_lookup_renames_field",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {"$project": {"renamed": "$lf"}},
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "renamed",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
        ],
        expected=[
            {"_id": 1, "renamed": "a", "j": [{"_id": 10, "ff": "a"}]},
        ],
        msg="$project before $lookup should allow joining on renamed field",
    ),
    LookupTestCase(
        "addfields_before_lookup",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "b"}],
        pipeline=[
            {"$addFields": {"new_lf": "b"}},
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "new_lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$project": {"j_count": {"$size": "$j"}}},
        ],
        expected=[{"_id": 1, "j_count": 1}],
        msg="$addFields before $lookup should allow joining on computed field",
    ),
    # Stages after $lookup.
    LookupTestCase(
        "lookup_then_match_filters_output",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "c"},
        ],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$match": {"j": {"$ne": []}}},
            {"$project": {"lf": 1}},
        ],
        expected=[{"_id": 1, "lf": "a"}],
        msg="$match after $lookup should filter on joined results",
    ),
    LookupTestCase(
        "lookup_then_sort_by_joined_count",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "b"},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "a"},
            {"_id": 11, "ff": "a"},
            {"_id": 12, "ff": "b"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$project": {"j_count": {"$size": "$j"}}},
            {"$sort": {"j_count": -1, "_id": 1}},
        ],
        expected=[
            {"_id": 1, "j_count": 2},
            {"_id": 2, "j_count": 1},
        ],
        msg="$sort after $lookup should order by joined result count",
    ),
    LookupTestCase(
        "lookup_then_project",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a", "x": 1}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$project": {"lf": 1, "x": {"$arrayElemAt": ["$j.x", 0]}}},
        ],
        expected=[{"_id": 1, "lf": "a", "x": 1}],
        msg="$project after $lookup should be able to extract from joined array",
    ),
    LookupTestCase(
        "lookup_then_unwind",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[
            {"_id": 10, "ff": "a", "x": 1},
            {"_id": 11, "ff": "a", "x": 2},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$unwind": "$j"},
            {"$project": {"x": "$j.x"}},
        ],
        expected=[
            {"_id": 1, "x": 1},
            {"_id": 1, "x": 2},
        ],
        msg="$unwind after $lookup should flatten the joined array",
    ),
    LookupTestCase(
        "lookup_then_unwind_exceeds_16mb",
        docs=[{"_id": 1, "lf": "m"}],
        foreign_docs=[{"_id": i, "ff": "m", "data": "x" * 1_000_000} for i in range(20)],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$unwind": "$j"},
            {"$count": "n"},
        ],
        expected=[{"n": 20}],
        msg="$unwind after $lookup should handle joined array exceeding 16MB",
    ),
    LookupTestCase(
        "lookup_then_group",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "b"},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "a", "x": 3},
            {"_id": 11, "ff": "a", "x": 7},
            {"_id": 12, "ff": "b", "x": 2},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$group": {"_id": "$lf", "total_x": {"$sum": {"$sum": "$j.x"}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "a", "total_x": 10},
            {"_id": "b", "total_x": 2},
        ],
        msg="$group after $lookup should aggregate over joined array fields",
    ),
    LookupTestCase(
        "lookup_then_replace_root",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a", "x": 42}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$replaceRoot": {"newRoot": {"$arrayElemAt": ["$j", 0]}}},
        ],
        expected=[{"_id": 10, "ff": "a", "x": 42}],
        msg="$replaceRoot after $lookup should promote first joined doc to root",
    ),
    # Multi-stage combinations.
    LookupTestCase(
        "match_sort_then_lookup",
        docs=[
            {"_id": 1, "lf": "a", "val": 10},
            {"_id": 2, "lf": "a", "val": 30},
            {"_id": 3, "lf": "a", "val": 20},
        ],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {"$match": {"val": {"$gte": 20}}},
            {"$sort": {"val": 1}},
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j",
                }
            },
            {"$project": {"val": 1, "j_count": {"$size": "$j"}}},
        ],
        expected=[
            {"_id": 3, "val": 20, "j_count": 1},
            {"_id": 2, "val": 30, "j_count": 1},
        ],
        msg="$match and $sort before $lookup should filter and order input",
    ),
    LookupTestCase(
        "sub_pipeline_then_project",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[
            {"_id": 10, "ff": "a", "x": 1},
            {"_id": 11, "ff": "a", "x": 5},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"lv": "$lf"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$ff", "$$lv"]}}},
                        {"$sort": {"x": -1}},
                        {"$limit": 1},
                    ],
                    "as": "top",
                }
            },
            {"$project": {"top_x": {"$arrayElemAt": ["$top.x", 0]}}},
        ],
        expected=[{"_id": 1, "top_x": 5}],
        msg="sub-pipeline $lookup with $sort/$limit then $project should return top match",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_PIPELINE_POSITION_TESTS))
def test_stages_position_lookup(collection, test_case: LookupTestCase):
    """Test $lookup composing with other stages at different pipeline positions."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
