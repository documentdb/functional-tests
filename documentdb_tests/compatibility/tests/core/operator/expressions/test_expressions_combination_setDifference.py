"""Combination tests for $setDifference composed with non-set operators and contexts."""

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
# $setDifference operands.
SETDIFFERENCE_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "concatArrays_input",
        expression={"$setDifference": [{"$concatArrays": [[1, 2], [3]]}, [2]]},
        expected=[1, 3],
        msg="$setDifference should accept a $concatArrays result as an operand",
    ),
    ExpressionTestCase(
        "filter_input",
        doc={"a": [1, 2, 3, 4]},
        expression={
            "$setDifference": [{"$filter": {"input": "$a", "cond": {"$gt": ["$$this", 2]}}}, [3]]
        },
        expected=[4],
        msg="$setDifference should accept a $filter result as an operand",
    ),
    ExpressionTestCase(
        "map_input",
        doc={"a": [1, 2, 3]},
        expression={
            "$setDifference": [{"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}}, [4]]
        },
        expected=[2, 6],
        msg="$setDifference should accept a $map result as an operand",
    ),
    ExpressionTestCase(
        "reverseArray_input",
        doc={"a": [1, 2, 3]},
        expression={"$setDifference": [{"$reverseArray": "$a"}, [2]]},
        expected=[3, 1],
        msg="$setDifference should accept a $reverseArray result as an operand",
    ),
    ExpressionTestCase(
        "cond_input",
        expression={"$setDifference": [{"$cond": [True, [1, 2, 3], []]}, [2]]},
        expected=[1, 3],
        msg="$setDifference should accept a $cond-produced array as an operand",
    ),
]

# Property [Self Composition]: $setDifference nests inside itself.
SETDIFFERENCE_SELF_COMPOSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "chained",
        expression={"$setDifference": [{"$setDifference": [["a", "b", "c"], ["a"]]}, ["b"]]},
        expected=["c"],
        msg="$setDifference should compose with another $setDifference",
    ),
    ExpressionTestCase(
        "self_nested",
        expression={"$setDifference": [{"$setDifference": [[1, 2, 3, 4], [1, 2]]}, [3]]},
        expected=[4],
        msg="$setDifference should nest inside itself",
    ),
    ExpressionTestCase(
        "deep_self_nested",
        expression={
            "$setDifference": [
                {"$setDifference": [{"$setDifference": [[1, 2, 3, 4, 5], [1]]}, [2]]},
                [3],
            ]
        },
        expected=[4, 5],
        msg="$setDifference should nest deeply inside itself",
    ),
]

# Property [Conditional And Binding Contexts]: $setDifference works inside $cond,
# $ifNull, and $let.
SETDIFFERENCE_CONTEXT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "in_cond_then",
        expression={"$cond": [True, {"$setDifference": [["a", "b"], ["a"]]}, []]},
        expected=["b"],
        msg="$setDifference should evaluate in a $cond then branch",
    ),
    ExpressionTestCase(
        "in_cond_else",
        expression={"$cond": [False, [], {"$setDifference": [["a", "b"], ["a"]]}]},
        expected=["b"],
        msg="$setDifference should evaluate in a $cond else branch",
    ),
    ExpressionTestCase(
        "ifnull_with_null",
        expression={"$ifNull": [{"$setDifference": [None, [1]]}, "fallback"]},
        expected="fallback",
        msg="$ifNull should return the fallback when $setDifference is null",
    ),
    ExpressionTestCase(
        "with_let",
        expression={
            "$let": {
                "vars": {"arr1": [1, 2, 3], "arr2": [2]},
                "in": {"$setDifference": ["$$arr1", "$$arr2"]},
            }
        },
        expected=[1, 3],
        msg="$setDifference should evaluate over $let-bound variables",
    ),
]

SETDIFFERENCE_COMBINATION_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_INPUT_TESTS + SETDIFFERENCE_SELF_COMPOSITION_TESTS + SETDIFFERENCE_CONTEXT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETDIFFERENCE_COMBINATION_TESTS))
def test_setDifference_combination(collection, test):
    """Test $setDifference combined with non-set operators and contexts."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_setDifference_in_match_expr(collection):
    """Test $setDifference in a $match $expr to filter documents."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2, 3], "b": [2, 3]},
            {"_id": 2, "a": [1, 2], "b": [1, 2]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$expr": {"$gt": [{"$size": {"$setDifference": ["$a", "$b"]}}, 0]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": [1, 2, 3], "b": [2, 3]}],
        msg="Should match documents where $setDifference is non-empty",
    )
