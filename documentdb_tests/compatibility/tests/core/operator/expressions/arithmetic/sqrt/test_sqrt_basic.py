"""
arithmetic $sqrt tests.

Tests for the arithmetic $sqrt operator: zero, perfect squares, and simple
decimal values, as literal expressions and as inserted document fields
(a representative subset).
"""

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

SQRT_BASIC_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        expression={"$sqrt": 0},
        expected=0.0,
        msg="sqrt(0) = 0.0 (int32 input returns double)",
    ),
    ExpressionTestCase(
        "double_zero",
        expression={"$sqrt": 0.0},
        expected=0.0,
        msg="sqrt(0.0) = 0.0",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        expression={"$sqrt": -0.0},
        expected=-0.0,
        msg="sqrt(-0.0) = -0.0 (preserves negative-zero sign)",
    ),
    ExpressionTestCase(
        "decimal_zero",
        expression={"$sqrt": Decimal128("0")},
        expected=Decimal128("0"),
        msg="sqrt(decimal 0) = 0 (type preserved)",
    ),
    ExpressionTestCase(
        "decimal_negative_zero",
        expression={"$sqrt": Decimal128("-0")},
        expected=Decimal128("-0"),
        msg="sqrt(decimal -0) = -0 (preserves negative-zero sign)",
    ),
    ExpressionTestCase(
        "int32_one",
        expression={"$sqrt": 1},
        expected=1.0,
        msg="sqrt(1) = 1.0",
    ),
    ExpressionTestCase(
        "int32_four",
        expression={"$sqrt": 4},
        expected=2.0,
        msg="sqrt(4) = 2.0 (int32 input)",
    ),
    ExpressionTestCase(
        "int32_nine",
        expression={"$sqrt": 9},
        expected=3.0,
        msg="sqrt(9) = 3.0",
    ),
    ExpressionTestCase(
        "int32_sixteen",
        expression={"$sqrt": 16},
        expected=4.0,
        msg="sqrt(16) = 4.0",
    ),
    ExpressionTestCase(
        "int32_hundred",
        expression={"$sqrt": 100},
        expected=10.0,
        msg="sqrt(100) = 10.0",
    ),
    ExpressionTestCase(
        "int64_four",
        expression={"$sqrt": Int64(4)},
        expected=2.0,
        msg="sqrt(4) = 2.0 (int64 input returns double)",
    ),
    ExpressionTestCase(
        "int64_hundred",
        expression={"$sqrt": Int64(100)},
        expected=10.0,
        msg="sqrt(100) = 10.0 (int64 input)",
    ),
    ExpressionTestCase(
        "double_four",
        expression={"$sqrt": 4.0},
        expected=2.0,
        msg="sqrt(4.0) = 2.0 (double input)",
    ),
    ExpressionTestCase(
        "double_quarter",
        expression={"$sqrt": 0.25},
        expected=0.5,
        msg="sqrt(0.25) = 0.5",
    ),
    ExpressionTestCase(
        "double_0_01",
        expression={"$sqrt": 0.01},
        expected=0.1,
        msg="sqrt(0.01) = 0.1",
    ),
    ExpressionTestCase(
        "decimal_four",
        expression={"$sqrt": Decimal128("4")},
        expected=Decimal128("2"),
        msg="sqrt(decimal 4) = 2 (decimal type preserved)",
    ),
    ExpressionTestCase(
        "decimal_nine",
        expression={"$sqrt": Decimal128("9")},
        expected=Decimal128("3"),
        msg="sqrt(decimal 9) = 3",
    ),
    ExpressionTestCase(
        "decimal_quarter",
        expression={"$sqrt": Decimal128("0.25")},
        expected=Decimal128("0.5"),
        msg="sqrt(decimal 0.25) = 0.5",
    ),
    ExpressionTestCase(
        "int32_two",
        expression={"$sqrt": 2},
        expected=pytest.approx(1.4142135623730951),
        msg="sqrt(2) ~= 1.41421 (irrational, double precision)",
    ),
    ExpressionTestCase(
        "int32_three",
        expression={"$sqrt": 3},
        expected=pytest.approx(1.7320508075688772),
        msg="sqrt(3) ~= 1.73205 (irrational)",
    ),
    ExpressionTestCase(
        "int32_five",
        expression={"$sqrt": 5},
        expected=pytest.approx(2.23606797749979),
        msg="sqrt(5) ~= 2.23607 (irrational)",
    ),
    ExpressionTestCase(
        "decimal_two",
        expression={"$sqrt": Decimal128("2")},
        expected=Decimal128("1.414213562373095048801688724209698"),
        msg="sqrt(decimal 2) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_three",
        expression={"$sqrt": Decimal128("3")},
        expected=Decimal128("1.732050807568877293527446341505872"),
        msg="sqrt(decimal 3) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_five",
        expression={"$sqrt": Decimal128("5")},
        expected=Decimal128("2.236067977499789696409173668731276"),
        msg="sqrt(decimal 5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "double_0_04",
        expression={"$sqrt": 0.04},
        expected=0.2,
        msg="sqrt(0.04) = 0.2",
    ),
    ExpressionTestCase(
        "double_0_09",
        expression={"$sqrt": 0.09},
        expected=0.3,
        msg="sqrt(0.09) = 0.3",
    ),
    ExpressionTestCase(
        "double_0_16",
        expression={"$sqrt": 0.16},
        expected=0.4,
        msg="sqrt(0.16) = 0.4",
    ),
    ExpressionTestCase(
        "double_0_36",
        expression={"$sqrt": 0.36},
        expected=0.6,
        msg="sqrt(0.36) = 0.6",
    ),
    ExpressionTestCase(
        "double_0_49",
        expression={"$sqrt": 0.49},
        expected=0.7,
        msg="sqrt(0.49) = 0.7",
    ),
    ExpressionTestCase(
        "double_0_64",
        expression={"$sqrt": 0.64},
        expected=0.8,
        msg="sqrt(0.64) = 0.8",
    ),
    ExpressionTestCase(
        "double_0_81",
        expression={"$sqrt": 0.81},
        expected=0.9,
        msg="sqrt(0.81) = 0.9",
    ),
    ExpressionTestCase(
        "decimal_0_04",
        expression={"$sqrt": Decimal128("0.04")},
        expected=Decimal128("0.2"),
        msg="sqrt(decimal 0.04) = 0.2",
    ),
    ExpressionTestCase(
        "decimal_0_09",
        expression={"$sqrt": Decimal128("0.09")},
        expected=Decimal128("0.3"),
        msg="sqrt(decimal 0.09) = 0.3",
    ),
    ExpressionTestCase(
        "decimal_0_16",
        expression={"$sqrt": Decimal128("0.16")},
        expected=Decimal128("0.4"),
        msg="sqrt(decimal 0.16) = 0.4",
    ),
    ExpressionTestCase(
        "decimal_0_36",
        expression={"$sqrt": Decimal128("0.36")},
        expected=Decimal128("0.6"),
        msg="sqrt(decimal 0.36) = 0.6",
    ),
    ExpressionTestCase(
        "decimal_0_49",
        expression={"$sqrt": Decimal128("0.49")},
        expected=Decimal128("0.7"),
        msg="sqrt(decimal 0.49) = 0.7",
    ),
    ExpressionTestCase(
        "decimal_0_64",
        expression={"$sqrt": Decimal128("0.64")},
        expected=Decimal128("0.8"),
        msg="sqrt(decimal 0.64) = 0.8",
    ),
    ExpressionTestCase(
        "decimal_0_81",
        expression={"$sqrt": Decimal128("0.81")},
        expected=Decimal128("0.9"),
        msg="sqrt(decimal 0.81) = 0.9",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SQRT_BASIC_LITERAL_TESTS))
def test_sqrt_basic_literal(collection, test):
    """Test $sqrt with literal zero, perfect-square, and simple decimal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


SQRT_BASIC_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_four",
        expression={"$sqrt": "$value"},
        doc={"value": 4},
        expected=2.0,
        msg="sqrt(4) = 2.0 (int32 input returns double)",
    ),
    ExpressionTestCase(
        "int64_hundred",
        expression={"$sqrt": "$value"},
        doc={"value": Int64(100)},
        expected=10.0,
        msg="sqrt(100) = 10.0 (int64 input)",
    ),
    ExpressionTestCase(
        "double_quarter",
        expression={"$sqrt": "$value"},
        doc={"value": 0.25},
        expected=0.5,
        msg="sqrt(0.25) = 0.5 (double input)",
    ),
    ExpressionTestCase(
        "decimal_nine",
        expression={"$sqrt": "$value"},
        doc={"value": Decimal128("9")},
        expected=Decimal128("3"),
        msg="sqrt(decimal 9) = 3 (decimal type preserved)",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        expression={"$sqrt": "$value"},
        doc={"value": -0.0},
        expected=-0.0,
        msg="sqrt(-0.0) = -0.0 (preserves negative-zero sign, via inserted field)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SQRT_BASIC_INSERT_TESTS))
def test_sqrt_basic_insert(collection, test):
    """Test $sqrt with inserted zero, perfect-square, and simple decimal values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
