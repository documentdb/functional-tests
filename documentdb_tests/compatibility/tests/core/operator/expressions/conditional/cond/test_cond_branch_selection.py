"""Tests for $cond branch selection — truthiness and falsiness of various types
as the condition, including boundary zero variants and expression results."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

TRUTHY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "true",
        expression={"$cond": [True, "then", "else"]},
        expected="then",
        msg="true is truthy",
    ),
    ExpressionTestCase(
        "int_1",
        expression={"$cond": [1, "then", "else"]},
        expected="then",
        msg="int 1 is truthy",
    ),
    ExpressionTestCase(
        "neg_int",
        expression={"$cond": [-1, "then", "else"]},
        expected="then",
        msg="negative int is truthy",
    ),
    ExpressionTestCase(
        "double_1",
        expression={"$cond": [1.0, "then", "else"]},
        expected="then",
        msg="double 1.0 is truthy",
    ),
    ExpressionTestCase(
        "string",
        expression={"$cond": ["abc", "then", "else"]},
        expected="then",
        msg="non-empty string is truthy",
    ),
    ExpressionTestCase(
        "empty_string",
        expression={"$cond": ["", "then", "else"]},
        expected="then",
        msg="empty string is truthy",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$cond": [[], "then", "else"]},
        expected="then",
        msg="empty array is truthy",
    ),
    ExpressionTestCase(
        "object",
        expression={"$cond": [{"a": 1}, "then", "else"]},
        expected="then",
        msg="object is truthy",
    ),
]

FALSY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false",
        expression={"$cond": [False, "then", "else"]},
        expected="else",
        msg="false is falsy",
    ),
    ExpressionTestCase(
        "null",
        expression={"$cond": [None, "then", "else"]},
        expected="else",
        msg="null is falsy",
    ),
    ExpressionTestCase(
        "int_0",
        expression={"$cond": [0, "then", "else"]},
        expected="else",
        msg="int 0 is falsy",
    ),
    ExpressionTestCase(
        "long_0",
        expression={"$cond": [Int64(0), "then", "else"]},
        expected="else",
        msg="long 0 is falsy",
    ),
    ExpressionTestCase(
        "double_0",
        expression={"$cond": [0.0, "then", "else"]},
        expected="else",
        msg="double 0.0 is falsy",
    ),
    ExpressionTestCase(
        "decimal_0",
        expression={"$cond": [Decimal128("0"), "then", "else"]},
        expected="else",
        msg="decimal 0 is falsy",
    ),
]

BOUNDARY_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_zero_double",
        expression={"$cond": [-0.0, "then", "else"]},
        expected="else",
        msg="negative zero double is falsy",
    ),
    ExpressionTestCase(
        "decimal_neg_zero",
        expression={"$cond": [Decimal128("-0"), "then", "else"]},
        expected="else",
        msg="decimal -0 is falsy",
    ),
    ExpressionTestCase(
        "decimal_0E10",
        expression={"$cond": [Decimal128("0E+10"), "then", "else"]},
        expected="else",
        msg="decimal 0E+10 is falsy",
    ),
    ExpressionTestCase(
        "decimal_0_0",
        expression={"$cond": [Decimal128("0.0"), "then", "else"]},
        expected="else",
        msg="decimal 0.0 is falsy",
    ),
    ExpressionTestCase(
        "tiny_double",
        expression={"$cond": [0.000000001, "then", "else"]},
        expected="then",
        msg="very small positive double is truthy",
    ),
    ExpressionTestCase(
        "smallest_decimal",
        expression={"$cond": [Decimal128("1E-6176"), "then", "else"]},
        expected="then",
        msg="smallest positive decimal128 is truthy",
    ),
]

EXPRESSION_RESULT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_0",
        expression={"$cond": [{"$literal": 0}, "then", "else"]},
        expected="else",
        msg="$literal 0 is falsy",
    ),
    ExpressionTestCase(
        "literal_1",
        expression={"$cond": [{"$literal": 1}, "then", "else"]},
        expected="then",
        msg="$literal 1 is truthy",
    ),
    ExpressionTestCase(
        "subtract_to_zero",
        expression={"$cond": [{"$subtract": [5, 5]}, "then", "else"]},
        expected="else",
        msg="$subtract 5-5=0 is falsy",
    ),
    ExpressionTestCase(
        "subtract_to_one",
        expression={"$cond": [{"$subtract": [5, 4]}, "then", "else"]},
        expected="then",
        msg="$subtract 5-4=1 is truthy",
    ),
]


ALL_TESTS = TRUTHY_TESTS + FALSY_TESTS + BOUNDARY_ZERO_TESTS + EXPRESSION_RESULT_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cond_truthiness(collection, test):
    """Test $cond truthiness — condition evaluation selects correct branch."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
