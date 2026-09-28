"""Combination tests for $setIsSubset composed with non-set operators and contexts."""

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
# $setIsSubset operands.
SETISSUBSET_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "concatArrays_input",
        expression={"$setIsSubset": [{"$concatArrays": [[1], [2]]}, [1, 2, 3]]},
        expected=True,
        msg="$setIsSubset should accept a $concatArrays result as the first operand",
    ),
    ExpressionTestCase(
        "filter_input",
        doc={"a": [1, 2, 3, 4], "b": [3, 4, 5]},
        expression={
            "$setIsSubset": [{"$filter": {"input": "$a", "cond": {"$gt": ["$$this", 2]}}}, "$b"]
        },
        expected=True,
        msg="$setIsSubset should accept a $filter result as the first operand",
    ),
    ExpressionTestCase(
        "map_input",
        doc={"a": [1, 2], "b": [2, 4, 6]},
        expression={
            "$setIsSubset": [{"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}}, "$b"]
        },
        expected=True,
        msg="$setIsSubset should accept a $map result as the first operand",
    ),
]

# Property [Conditional And Binding Contexts]: $setIsSubset drives $cond, composes
# under $and/$or/$not, and evaluates over $let-bound variables.
SETISSUBSET_CONTEXT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "in_cond_true",
        doc={"a": [1, 2], "b": [1, 2, 3]},
        expression={"$cond": {"if": {"$setIsSubset": ["$a", "$b"]}, "then": "yes", "else": "no"}},
        expected="yes",
        msg="$setIsSubset should drive a $cond then branch when the first is a subset",
    ),
    ExpressionTestCase(
        "in_cond_false",
        doc={"a": [1, 2, 3], "b": [1, 2]},
        expression={"$cond": {"if": {"$setIsSubset": ["$a", "$b"]}, "then": "yes", "else": "no"}},
        expected="no",
        msg="$setIsSubset should drive a $cond else branch when the first is not a subset",
    ),
    ExpressionTestCase(
        "in_and_mutual_subset",
        doc={"a": [1, 2], "b": [1, 2]},
        expression={"$and": [{"$setIsSubset": ["$a", "$b"]}, {"$setIsSubset": ["$b", "$a"]}]},
        expected=True,
        msg="$and should combine mutual $setIsSubset checks into a set-equality test",
    ),
    ExpressionTestCase(
        "in_or_one_subset",
        doc={"a": [1, 2], "b": [1, 2, 3]},
        expression={"$or": [{"$setIsSubset": ["$a", "$b"]}, {"$setIsSubset": ["$b", "$a"]}]},
        expected=True,
        msg="$or should be true when one direction of $setIsSubset holds",
    ),
    ExpressionTestCase(
        "in_not",
        doc={"a": [1, 2, 3], "b": [1, 2]},
        expression={"$not": [{"$setIsSubset": ["$a", "$b"]}]},
        expected=True,
        msg="$not should negate a false $setIsSubset result",
    ),
    ExpressionTestCase(
        "with_let",
        expression={
            "$let": {
                "vars": {"arr1": [1, 2], "arr2": [1, 2, 3]},
                "in": {"$setIsSubset": ["$$arr1", "$$arr2"]},
            }
        },
        expected=True,
        msg="$setIsSubset should evaluate over $let-bound variables",
    ),
]

SETISSUBSET_COMBINATION_TESTS: list[ExpressionTestCase] = (
    SETISSUBSET_INPUT_TESTS + SETISSUBSET_CONTEXT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETISSUBSET_COMBINATION_TESTS))
def test_setIsSubset_combination(collection, test):
    """Test $setIsSubset combined with non-set operators and contexts."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_setIsSubset_in_match_expr(collection):
    """Test $setIsSubset in a $match $expr to filter documents."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2], "b": [1, 2, 3]},
            {"_id": 2, "a": [1, 2, 4], "b": [1, 2, 3]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$expr": {"$setIsSubset": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": [1, 2], "b": [1, 2, 3]}],
        msg="Should match documents where the first array is a subset of the second",
    )
