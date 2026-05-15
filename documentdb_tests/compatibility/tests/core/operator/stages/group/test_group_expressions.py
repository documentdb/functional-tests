"""Aggregation $group stage tests - accumulator expressions and system variables."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Accumulator Expression Acceptance]: accumulator expressions accept
# expressions (verified by one representative, $cond), and a nested
# accumulator in expression position (inner $sum sums an array, outer $sum is
# the accumulator).
GROUP_ACCUMULATOR_EXPRESSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accumulator_cond_expression",
        docs=[
            {"_id": 1, "g": "a", "x": 10},
            {"_id": 2, "g": "a", "x": -5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$g",
                    "r": {"$sum": {"$cond": [{"$gte": ["$x", 0]}, "$x", 0]}},
                }
            }
        ],
        expected=[{"_id": "a", "r": 10}],
        msg="Accumulator with $cond expression should evaluate per document",
    ),
    StageTestCase(
        id="nested_accumulator_in_expression_position",
        docs=[
            {"_id": 1, "g": "a", "v": [1, 2, 3]},
            {"_id": 2, "g": "a", "v": [4, 5]},
        ],
        pipeline=[{"$group": {"_id": "$g", "r": {"$sum": {"$sum": "$v"}}}}],
        expected=[{"_id": "a", "r": 15}],
        msg=(
            "Nested accumulator in expression position: inner $sum sums the"
            " array, outer $sum accumulates across documents"
        ),
    ),
]

# Property [System Variables in Expressions]: test both $$ROOT and $$CURRENT
# work in accumulator expressions and _id, $literal prevents field reference
# interpretation in both _id and accumulator expressions, and $$REMOVE in
# $push produces an empty array.
GROUP_SYSTEM_VARIABLE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="push_root_collects_full_docs",
        docs=[
            {"_id": 1, "g": "a", "x": 10},
            {"_id": 2, "g": "a", "x": 20},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$g", "r": {"$push": "$$ROOT"}}},
        ],
        expected=[
            {
                "_id": "a",
                "r": [
                    {"_id": 1, "g": "a", "x": 10},
                    {"_id": 2, "g": "a", "x": 20},
                ],
            }
        ],
        msg="$$ROOT in $push should collect full input documents",
    ),
    StageTestCase(
        id="push_current_collects_full_docs",
        docs=[
            {"_id": 1, "g": "a", "x": 10},
            {"_id": 2, "g": "a", "x": 20},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$g", "r": {"$push": "$$CURRENT"}}},
        ],
        expected=[
            {
                "_id": "a",
                "r": [
                    {"_id": 1, "g": "a", "x": 10},
                    {"_id": 2, "g": "a", "x": 20},
                ],
            }
        ],
        msg="$$CURRENT in $push should collect full input documents",
    ),
    StageTestCase(
        id="root_in_id_groups_by_entire_doc",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2, "x": 20},
            {"_id": 3, "x": 10},
        ],
        pipeline=[{"$group": {"_id": "$$ROOT", "count": {"$sum": 1}}}],
        expected=[
            {"_id": {"_id": 1, "x": 10}, "count": 1},
            {"_id": {"_id": 2, "x": 20}, "count": 1},
            {"_id": {"_id": 3, "x": 10}, "count": 1},
        ],
        msg="$$ROOT in _id should group by the entire input document",
    ),
    StageTestCase(
        id="current_in_id_groups_by_entire_doc",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2, "x": 20},
            {"_id": 3, "x": 10},
        ],
        pipeline=[{"$group": {"_id": "$$CURRENT", "count": {"$sum": 1}}}],
        expected=[
            {"_id": {"_id": 1, "x": 10}, "count": 1},
            {"_id": {"_id": 2, "x": 20}, "count": 1},
            {"_id": {"_id": 3, "x": 10}, "count": 1},
        ],
        msg="$$CURRENT in _id should group by the entire input document",
    ),
    StageTestCase(
        id="literal_prevents_field_ref_in_id",
        docs=[{"_id": 1, "v": "hello"}, {"_id": 2, "v": "world"}],
        pipeline=[{"$group": {"_id": {"$literal": "$v"}, "count": {"$sum": 1}}}],
        expected=[{"_id": "$v", "count": 2}],
        msg=(
            "$literal in _id should prevent field reference interpretation,"
            " treating '$v' as a string constant"
        ),
    ),
    StageTestCase(
        id="literal_prevents_field_ref_in_accumulator",
        docs=[{"_id": 1, "g": "a"}, {"_id": 2, "g": "a"}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$g",
                    "r": {"$push": {"$literal": "$nonexistent"}},
                }
            },
        ],
        expected=[{"_id": "a", "r": ["$nonexistent", "$nonexistent"]}],
        msg=(
            "$literal in accumulator should prevent field reference"
            " interpretation, treating '$nonexistent' as a string constant"
        ),
    ),
    StageTestCase(
        id="remove_in_push_produces_empty_array",
        docs=[{"_id": 1, "g": "a"}, {"_id": 2, "g": "a"}],
        pipeline=[{"$group": {"_id": "$g", "r": {"$push": "$$REMOVE"}}}],
        expected=[{"_id": "a", "r": []}],
        msg="$$REMOVE in $push should produce an empty array, not an array of nulls",
    ),
]

GROUP_EXPRESSION_ARGS_TESTS = GROUP_ACCUMULATOR_EXPRESSION_TESTS + GROUP_SYSTEM_VARIABLE_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_EXPRESSION_ARGS_TESTS))
def test_group_expressions(collection, test_case: StageTestCase):
    """Test $group stage - accumulator expressions and system variables."""
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
