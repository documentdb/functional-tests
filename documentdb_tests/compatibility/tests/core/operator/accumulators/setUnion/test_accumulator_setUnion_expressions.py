"""Tests for $setUnion accumulator: expression types."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
    sort_array_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Type]: $setUnion accepts various expression types as its
# argument in $group context — literals, field paths, nested field paths,
# expression operators, and conditional expressions.
SETUNION_EXPRESSION_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_literal_array",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$literal": [10, 20]}},
                }
            },
            sort_array_project("result"),
        ],
        expected=[{"result": [10, 20]}],
        msg="$setUnion should accept $literal array expression",
    ),
    AccumulatorTestCase(
        "expr_field_path",
        docs=[{"v": [1, 2]}, {"v": [2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            sort_array_project("result"),
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should accept simple field path expression",
    ),
    AccumulatorTestCase(
        "expr_nested_field_path",
        docs=[{"a": {"b": [1, 2]}}, {"a": {"b": [2, 3]}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$a.b"}}},
            sort_array_project("result"),
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should accept nested field path expression",
    ),
    AccumulatorTestCase(
        "expr_expression_operator",
        docs=[{"v": [1, 2, 2, 3]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$setUnion": ["$v", [4]]}},
                }
            },
            sort_array_project("result"),
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should accept expression operator ($setUnion expression) as argument",
    ),
    AccumulatorTestCase(
        "expr_cond_expression",
        docs=[
            {"v": [1, 2], "use": True},
            {"v": [3, 4], "use": False},
            {"v": [5, 6], "use": True},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$cond": ["$use", "$v", "$$REMOVE"],
                        }
                    },
                }
            },
            sort_array_project("result"),
        ],
        expected=[{"result": [1, 2, 5, 6]}],
        msg="$setUnion should accept $cond expression as argument",
    ),
    AccumulatorTestCase(
        "expr_object_expression",
        docs=[{"v": [1, 2]}, {"v": [2, 3]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {"$ifNull": ["$v", []]},
                    },
                }
            },
            sort_array_project("result"),
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should accept object expression ($ifNull) as argument",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_EXPRESSION_TYPE_TESTS))
def test_accumulator_setUnion_expressions(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator expression type handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
