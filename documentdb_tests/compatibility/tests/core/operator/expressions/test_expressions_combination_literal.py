"""
Integration tests for $literal with sibling expression operators.

Covers $literal with $type/$cond/$ifNull, $literal suppression inside $let,
and $literal dollar-sign comparison via $eq.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# $literal with $type
# ---------------------------------------------------------------------------
LITERAL_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "type_int",
        expression={"$type": {"$literal": 42}},
        expected="int",
        msg="$type of $literal int should return 'int'",
    ),
    ExpressionTestCase(
        "type_double",
        expression={"$type": {"$literal": 2.5}},
        expected="double",
        msg="$type of $literal double should return 'double'",
    ),
    ExpressionTestCase(
        "type_string",
        expression={"$type": {"$literal": "hello"}},
        expected="string",
        msg="$type of $literal string should return 'string'",
    ),
    ExpressionTestCase(
        "type_bool",
        expression={"$type": {"$literal": True}},
        expected="bool",
        msg="$type of $literal bool should return 'bool'",
    ),
    ExpressionTestCase(
        "type_null",
        expression={"$type": {"$literal": None}},
        expected="null",
        msg="$type of $literal null should return 'null'",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TYPE_TESTS))
def test_literal_type_verification(collection, test):
    """Test $type returns correct type name for $literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# $literal with $cond and $ifNull
# ---------------------------------------------------------------------------
def test_literal_in_cond_then(collection):
    """Test $literal used in $cond then branch."""
    result = execute_expression(
        collection,
        {"$cond": [True, {"$literal": {"$add": [1, 2]}}, "no"]},
    )
    assert_expression_result(
        result,
        expected={"$add": [1, 2]},
        msg="$literal in $cond then should return unevaluated expression object",
    )


def test_literal_in_cond_else(collection):
    """Test $literal used in $cond else branch."""
    result = execute_expression(
        collection,
        {"$cond": [False, "yes", {"$literal": "$fieldPath"}]},
    )
    assert_expression_result(
        result,
        expected="$fieldPath",
        msg="$literal in $cond else should return string, not field value",
    )


def test_literal_in_ifnull_fallback(collection):
    """Test $literal used as $ifNull fallback value."""
    result = execute_expression(
        collection,
        {"$ifNull": [None, {"$literal": {"$add": [1, 2]}}]},
    )
    assert_expression_result(
        result,
        expected={"$add": [1, 2]},
        msg="$literal as $ifNull fallback should return unevaluated expression object",
    )


# ---------------------------------------------------------------------------
# $literal suppression inside $let
# ---------------------------------------------------------------------------
def test_literal_suppresses_variable_in_let(collection):
    """Test $literal in $let 'in' returns string '$$x', not variable value."""
    result = execute_expression(
        collection,
        {"$let": {"vars": {"x": 42}, "in": {"$literal": "$$x"}}},
    )
    assert_expression_result(
        result,
        expected="$$x",
        msg="$literal should return string '$$x', not variable value",
    )


# ---------------------------------------------------------------------------
# $literal dollar-sign string comparison via $eq
# ---------------------------------------------------------------------------
def test_literal_dollar_string_eq_match(collection):
    """Test $literal '$1' compared via $eq to field containing '$1' returns true."""
    collection.insert_one({"_id": 1, "price": "$1"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$eq": ["$price", {"$literal": "$1"}]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"result": True}], msg="$literal '$1' should match field containing '$1'"
    )


def test_literal_dollar_string_eq_no_match(collection):
    """Test $literal '$1' compared via $eq to field not containing '$1' returns false."""
    collection.insert_one({"_id": 1, "price": "$2.50"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$eq": ["$price", {"$literal": "$1"}]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"result": False}],
        msg="$literal '$1' should not match field containing '$2.50'",
    )
