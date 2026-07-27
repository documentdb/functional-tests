"""Combination tests for $setEquals composed with non-set operators and contexts."""

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
# $setEquals operands.
SETEQUALS_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "concatArrays_input",
        expression={"$setEquals": [{"$concatArrays": [[1], [2]]}, [1, 2]]},
        expected=True,
        msg="$setEquals should accept a $concatArrays result as an operand",
    ),
    ExpressionTestCase(
        "filter_input",
        doc={"a": [1, 2, 3, 4]},
        expression={
            "$setEquals": [{"$filter": {"input": "$a", "cond": {"$gt": ["$$this", 2]}}}, [3, 4]]
        },
        expected=True,
        msg="$setEquals should accept a $filter result as an operand",
    ),
    ExpressionTestCase(
        "map_input",
        doc={"a": [1, 2, 3]},
        expression={
            "$setEquals": [{"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}}, [2, 4, 6]]
        },
        expected=True,
        msg="$setEquals should accept a $map result as an operand",
    ),
]

# Property [Conditional And Binding Contexts]: $setEquals works inside $cond,
# $let, and $not.
SETEQUALS_CONTEXT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "in_cond_true",
        doc={"a": [1, 2], "b": [2, 1]},
        expression={
            "$cond": {"if": {"$setEquals": ["$a", "$b"]}, "then": "match", "else": "no_match"}
        },
        expected="match",
        msg="$setEquals should drive a $cond then branch when the sets are equal",
    ),
    ExpressionTestCase(
        "in_cond_false",
        doc={"a": [1, 2], "b": [3, 4]},
        expression={
            "$cond": {"if": {"$setEquals": ["$a", "$b"]}, "then": "match", "else": "no_match"}
        },
        expected="no_match",
        msg="$setEquals should drive a $cond else branch when the sets differ",
    ),
    ExpressionTestCase(
        "with_let",
        expression={
            "$let": {
                "vars": {"arr1": [1, 2, 3], "arr2": [3, 2, 1]},
                "in": {"$setEquals": ["$$arr1", "$$arr2"]},
            }
        },
        expected=True,
        msg="$setEquals should evaluate over $let-bound variables",
    ),
    ExpressionTestCase(
        "in_not",
        doc={"a": [1, 2], "b": [3, 4]},
        expression={"$not": [{"$setEquals": ["$a", "$b"]}]},
        expected=True,
        msg="$not should negate a false $setEquals result",
    ),
]

SETEQUALS_COMBINATION_TESTS: list[ExpressionTestCase] = (
    SETEQUALS_INPUT_TESTS + SETEQUALS_CONTEXT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETEQUALS_COMBINATION_TESTS))
def test_setEquals_combination(collection, test):
    """Test $setEquals combined with non-set operators and contexts."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_setEquals_in_match_expr(collection):
    """Test $setEquals in a $match $expr to filter documents."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2], "b": [2, 1]},
            {"_id": 2, "a": [1, 2], "b": [3, 4]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$expr": {"$setEquals": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": [1, 2], "b": [2, 1]}],
        msg="Should match documents where $setEquals is true",
    )
