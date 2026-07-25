"""Combination tests for $setIntersection composed with non-set operators and contexts."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Array-Producing Inputs]: operators that produce arrays can feed
# $setIntersection operands.
SETINTERSECTION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "concatArrays_input",
        expression={"$setIntersection": [{"$concatArrays": [[1, 2], [3]]}, [2, 3, 4]]},
        expected=[2, 3],
        msg="$setIntersection should accept a $concatArrays result as an operand",
    ),
    ExpressionTestCase(
        "filter_input",
        doc={"a": [1, 2, 3, 4]},
        expression={
            "$setIntersection": [
                {"$filter": {"input": "$a", "cond": {"$gt": ["$$this", 1]}}},
                [2, 4],
            ]
        },
        expected=[2, 4],
        msg="$setIntersection should accept a $filter result as an operand",
    ),
    ExpressionTestCase(
        "map_input",
        doc={"a": [1, 2, 3]},
        expression={
            "$setIntersection": [
                {"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}},
                [4, 6],
            ]
        },
        expected=[4, 6],
        msg="$setIntersection should accept a $map result as an operand",
    ),
]

# Property [Self Composition]: $setIntersection nests inside itself.
SETINTERSECTION_SELF_COMPOSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "self_nested",
        expression={"$setIntersection": [{"$setIntersection": [[1, 2, 3], [2, 3, 4]]}, [2, 5]]},
        expected=[2],
        msg="$setIntersection should nest inside itself",
    ),
]

# Property [Conditional And Binding Contexts]: $setIntersection works inside
# $cond, $let, and $ifNull.
SETINTERSECTION_CONTEXT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "in_cond",
        doc={"a": [1, 2], "b": [2, 3]},
        expression={
            "$cond": {
                "if": {"$gt": [{"$size": {"$setIntersection": ["$a", "$b"]}}, 0]},
                "then": "overlap",
                "else": "disjoint",
            }
        },
        expected="overlap",
        msg="$setIntersection should drive a $cond branch on intersection size",
    ),
    ExpressionTestCase(
        "in_let",
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expression={
            "$let": {
                "vars": {"common": {"$setIntersection": ["$a", "$b"]}},
                "in": {"$size": "$$common"},
            }
        },
        expected=2,
        msg="$setIntersection should bind to a $let variable",
    ),
    ExpressionTestCase(
        "ifnull_with_null",
        expression={"$ifNull": [{"$setIntersection": [None, [1]]}, "fallback"]},
        expected="fallback",
        msg="$ifNull should return the fallback when $setIntersection is null",
    ),
]

SETINTERSECTION_COMBINATION_TESTS: list[ExpressionTestCase] = (
    SETINTERSECTION_INPUT_TESTS
    + SETINTERSECTION_SELF_COMPOSITION_TESTS
    + SETINTERSECTION_CONTEXT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETINTERSECTION_COMBINATION_TESTS))
def test_setIntersection_combination(collection, test):
    """Test $setIntersection combined with non-set operators and contexts."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg, ignore_order=True)


def test_setIntersection_in_match_expr(collection):
    """Test $setIntersection in a $match $expr to filter documents."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2, 3], "b": [2, 3]},
            {"_id": 2, "a": [1, 2], "b": [3, 4]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$expr": {"$gt": [{"$size": {"$setIntersection": ["$a", "$b"]}}, 0]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": [1, 2, 3], "b": [2, 3]}],
        msg="Should match documents where $setIntersection is non-empty",
    )
