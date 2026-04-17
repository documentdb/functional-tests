"""
Combination tests for boolean expression operators ($and, $or, $not).

Tests $and, $or, and $not combined with each other, comparison, and arithmetic
expressions to verify correct boolean evaluation in nested/mixed contexts.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

OR_WITH_AND_TESTS = [
    ExpressionTestCase(
        "or_and_true",
        expression={"$or": [{"$and": [True, True]}, False]},
        expected=True,
        msg="$or should return true when nested $and is true",
    ),
    ExpressionTestCase(
        "or_and_false",
        expression={"$or": [{"$and": [True, False]}, False]},
        expected=False,
        msg="$or should return false when nested $and and other arg are both false",
    ),
]

OR_WITH_NOT_TESTS = [
    ExpressionTestCase(
        "or_not_mixed",
        expression={"$or": [{"$not": [True]}, True]},
        expected=True,
        msg="$or with one $not(false) and one literal true = true",
    ),
    ExpressionTestCase(
        "or_not_all_false",
        expression={"$or": [{"$not": [True]}, {"$not": [True]}]},
        expected=False,
        msg="$or with $not args: false OR false = false",
    ),
]

OR_WITH_COMPARISON_TESTS = [
    ExpressionTestCase(
        "or_gt_lt",
        expression={"$or": [{"$gt": [1, 2]}, {"$lt": [1, 2]}]},
        expected=True,
        msg="$or with $gt(false) and $lt(true) should return true",
    ),
    ExpressionTestCase(
        "or_eq_ne",
        expression={"$or": [{"$eq": [1, 2]}, {"$ne": [1, 2]}]},
        expected=True,
        msg="$or with $eq(false) and $ne(true) should return true",
    ),
    ExpressionTestCase(
        "or_all_comparisons_false",
        expression={"$or": [{"$gt": [1, 2]}, {"$eq": [1, 2]}]},
        expected=False,
        msg="$or with all false comparisons should return false",
    ),
]

OR_WITH_ARITHMETIC_TESTS = [
    ExpressionTestCase(
        "or_add_nonzero",
        expression={"$or": [{"$add": [1, 2]}]},
        expected=True,
        msg="$or with $add producing 3 should return true",
    ),
    ExpressionTestCase(
        "or_multiply_zero",
        expression={"$or": [{"$multiply": [5, 0]}, False]},
        expected=False,
        msg="$or with $multiply producing 0 and false should return false",
    ),
]

OR_DEEP_NESTING_TESTS = [
    ExpressionTestCase(
        "or_and_not",
        expression={"$or": [{"$and": [{"$not": [False]}, True]}, False]},
        expected=True,
        msg="$or($and($not(false), true), false) should return true",
    ),
    ExpressionTestCase(
        "or_deep_all_false",
        expression={"$or": [{"$and": [{"$not": [True]}, False]}, {"$and": [False, False]}]},
        expected=False,
        msg="Deeply nested all-false should return false",
    ),
]

NOT_WITH_AND_TESTS = [
    ExpressionTestCase(
        "not_and_true",
        expression={"$not": [{"$and": [True, True]}]},
        expected=False,
        msg="$not($and(true, true)) should return false",
    ),
]

NOT_WITH_OR_TESTS = [
    ExpressionTestCase(
        "not_or_false",
        expression={"$not": [{"$or": [False, False]}]},
        expected=True,
        msg="$not($or(false, false)) should return true",
    ),
]

NOT_WITH_COMPARISON_TESTS = [
    ExpressionTestCase(
        "not_eq_true",
        expression={"$not": [{"$eq": [1, 1]}]},
        expected=False,
        msg="$not($eq(1, 1)) should return false",
    ),
]

NOT_WITH_ARITHMETIC_TESTS = [
    ExpressionTestCase(
        "not_subtract_zero",
        expression={"$not": [{"$subtract": [3, 3]}]},
        expected=True,
        msg="$not($subtract(3, 3)) should return true, 0 is falsy",
    ),
]

NOT_DEEP_NESTING_TESTS = [
    ExpressionTestCase(
        "not_and_or_comparison",
        expression={"$not": [{"$and": [{"$gt": [10, 5]}, {"$or": [False, True]}]}]},
        expected=False,
        msg="$not($and($gt(10,5), $or(false, true))) should return false",
    ),
]

AND_WITH_OR_TESTS = [
    ExpressionTestCase(
        "and_or_false",
        expression={"$and": [{"$or": [False, False]}, True]},
        expected=False,
        msg="$and should return false when nested $or is false",
    ),
    ExpressionTestCase(
        "and_arithmetic_coercion",
        expression={"$and": [{"$add": [1, 2]}, {"$multiply": [5, 0]}]},
        expected=False,
        msg="$and with $add(3) and $multiply(0) should return false",
    ),
    ExpressionTestCase(
        "and_not_comparison",
        expression={"$and": [{"$not": [False]}, {"$gt": [10, 5]}]},
        expected=True,
        msg="$and with $not(false)=true and $gt(true) should return true",
    ),
    ExpressionTestCase(
        "and_all_expression_args_false",
        expression={"$and": [{"$gt": [1, 2]}, {"$or": [False, False]}]},
        expected=False,
        msg="$and where all expression args evaluate false should return false",
    ),
    ExpressionTestCase(
        "and_or_not_three_way",
        expression={"$and": [{"$or": [False, True]}, {"$not": [False]}]},
        expected=True,
        msg="$and($or(false,true)=true, $not(false)=true) should return true",
    ),
]

ALL_TESTS = (
    OR_WITH_AND_TESTS
    + OR_WITH_NOT_TESTS
    + OR_WITH_COMPARISON_TESTS
    + OR_WITH_ARITHMETIC_TESTS
    + OR_DEEP_NESTING_TESTS
    + AND_WITH_OR_TESTS
    + NOT_WITH_AND_TESTS
    + NOT_WITH_OR_TESTS
    + NOT_WITH_COMPARISON_TESTS
    + NOT_WITH_ARITHMETIC_TESTS
    + NOT_DEEP_NESTING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_expressions_combination_boolean(collection, test):
    """Test boolean expression operators combined with other expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
