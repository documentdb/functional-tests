"""Tests for $not truthiness across BSON types and return type verification."""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN, MISSING

FALSY_TESTS = [
    ExpressionTestCase(
        "not_truth_false",
        expression={"$not": [False]},
        expected=True,
        msg="false is falsy",
    ),
    ExpressionTestCase(
        "not_truth_int_zero",
        expression={"$not": [0]},
        expected=True,
        msg="int 0 is falsy",
    ),
    ExpressionTestCase(
        "not_truth_int64_zero",
        expression={"$not": [Int64(0)]},
        expected=True,
        msg="Int64 0 is falsy",
    ),
    ExpressionTestCase(
        "not_truth_double_zero",
        expression={"$not": [0.0]},
        expected=True,
        msg="double 0.0 is falsy",
    ),
    ExpressionTestCase(
        "not_truth_decimal_zero",
        expression={"$not": [Decimal128("0")]},
        expected=True,
        msg="decimal128 0 is falsy",
    ),
    ExpressionTestCase(
        "not_truth_missing_field",
        expression={"$not": [MISSING]},
        expected=True,
        msg="missing field is falsy",
    ),
]

TRUTHY_TESTS = [
    ExpressionTestCase(
        "not_truth_true",
        expression={"$not": [True]},
        expected=False,
        msg="true is truthy",
    ),
    ExpressionTestCase(
        "not_truth_int_1",
        expression={"$not": [1]},
        expected=False,
        msg="int 1 is truthy",
    ),
    ExpressionTestCase(
        "not_truth_neg_int",
        expression={"$not": [-1]},
        expected=False,
        msg="negative int is truthy",
    ),
    ExpressionTestCase(
        "not_truth_double_1_5",
        expression={"$not": [1.5]},
        expected=False,
        msg="double 1.5 is truthy",
    ),
    ExpressionTestCase(
        "not_truth_empty_string",
        expression={"$not": [""]},
        expected=False,
        msg="empty string is truthy",
    ),
    ExpressionTestCase(
        "not_truth_non_empty_string",
        expression={"$not": ["hello"]},
        expected=False,
        msg="non-empty string is truthy",
    ),
    ExpressionTestCase(
        "not_truth_empty_array",
        expression={"$not": [[]]},
        expected=False,
        msg="empty array is truthy",
    ),
    ExpressionTestCase(
        "not_truth_empty_object",
        expression={"$not": [{}]},
        expected=False,
        msg="empty object is truthy",
    ),
    ExpressionTestCase(
        "not_truth_date",
        expression={"$not": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        expected=False,
        msg="date is truthy",
    ),
    ExpressionTestCase(
        "not_truth_minkey",
        expression={"$not": [MinKey()]},
        expected=False,
        msg="MinKey is truthy",
    ),
    ExpressionTestCase(
        "not_truth_maxkey",
        expression={"$not": [MaxKey()]},
        expected=False,
        msg="MaxKey is truthy",
    ),
    ExpressionTestCase(
        "not_truth_objectid",
        expression={"$not": [ObjectId()]},
        expected=False,
        msg="ObjectId is truthy",
    ),
    ExpressionTestCase(
        "not_truth_float_nan",
        expression={"$not": [FLOAT_NAN]},
        expected=False,
        msg="NaN is truthy",
    ),
]

ALL_TESTS = FALSY_TESTS + TRUTHY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_truthiness_literal(collection, test):
    """Test $not truthiness with literal values across BSON types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


RETURN_TYPE_TESTS = [
    ExpressionTestCase(
        "return_type_true",
        expression={"$not": [False]},
        expected="bool",
        msg="Should return bool type for truthy result",
    ),
    ExpressionTestCase(
        "return_type_false",
        expression={"$not": [True]},
        expected="bool",
        msg="Should return bool type for falsy result",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RETURN_TYPE_TESTS))
def test_not_return_type(collection, test):
    """Test $not return type."""
    result = execute_expression(collection, {"$type": test.expression})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
