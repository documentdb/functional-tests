"""
Basic rounding tests for $round expression.

Covers zero/positive/negative values for all numeric types, rounding
direction (up/down), and round-to-even (banker's rounding) behavior.
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
from documentdb_tests.framework.test_constants import (
    DOUBLE_HALF,
    DOUBLE_TWO_AND_HALF,
)

ROUND_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        expression={"$round": 0},
        expected=0,
        msg="int32 0 rounds to int32 0 (type preserved)",
    ),
    ExpressionTestCase(
        "int64_zero",
        expression={"$round": Int64(0)},
        expected=Int64(0),
        msg="int64 0 rounds to int64 0 (type preserved)",
    ),
    ExpressionTestCase(
        "double_zero",
        expression={"$round": 0.0},
        expected=0.0,
        msg="double 0.0 rounds to double 0.0",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        expression={"$round": -0.0},
        expected=-0.0,
        msg="double -0.0 preserves the negative-zero sign",
    ),
    ExpressionTestCase(
        "decimal_zero",
        expression={"$round": Decimal128("0")},
        expected=Decimal128("0"),
        msg="decimal 0 rounds to decimal 0 (type preserved)",
    ),
    ExpressionTestCase(
        "decimal_negative_zero",
        expression={"$round": Decimal128("-0")},
        expected=Decimal128("-0"),
        msg="decimal -0 preserves the negative-zero sign",
    ),
    ExpressionTestCase(
        "int32_positive",
        expression={"$round": 1},
        expected=1,
        msg="int32 1 is already integral and is returned unchanged",
    ),
    ExpressionTestCase(
        "int64_positive",
        expression={"$round": Int64(1)},
        expected=Int64(1),
        msg="int64 1 is already integral and is returned unchanged",
    ),
    ExpressionTestCase(
        "int32_negative",
        expression={"$round": -1},
        expected=-1,
        msg="int32 -1 is already integral and is returned unchanged",
    ),
    ExpressionTestCase(
        "int64_negative",
        expression={"$round": Int64(-1)},
        expected=Int64(-1),
        msg="int64 -1 is already integral and is returned unchanged",
    ),
    ExpressionTestCase(
        "double_positive",
        expression={"$round": 1.5},
        expected=2.0,
        msg="double 1.5 rounds half-to-even up to 2.0",
    ),
    ExpressionTestCase(
        "double_negative",
        expression={"$round": -1.5},
        expected=-2.0,
        msg="double -1.5 rounds half-to-even to -2.0",
    ),
    ExpressionTestCase(
        "double_round_down",
        expression={"$round": 1.4},
        expected=1.0,
        msg="double 1.4 is below midpoint and rounds down to 1.0",
    ),
    ExpressionTestCase(
        "double_round_up",
        expression={"$round": 1.6},
        expected=2.0,
        msg="double 1.6 is above midpoint and rounds up to 2.0",
    ),
    ExpressionTestCase(
        "decimal_positive",
        expression={"$round": Decimal128("1.5")},
        expected=Decimal128("2"),
        msg="decimal 1.5 rounds half-to-even up to 2",
    ),
    ExpressionTestCase(
        "decimal_negative",
        expression={"$round": Decimal128("-1.5")},
        expected=Decimal128("-2"),
        msg="decimal -1.5 rounds half-to-even to -2",
    ),
    ExpressionTestCase(
        "round_to_even_10_5",
        expression={"$round": 10.5},
        expected=10.0,
        msg="10.5 rounds half-to-even down to 10.0",
    ),
    ExpressionTestCase(
        "round_to_even_11_5",
        expression={"$round": 11.5},
        expected=12.0,
        msg="11.5 rounds half-to-even up to 12.0",
    ),
    ExpressionTestCase(
        "round_to_even_12_5",
        expression={"$round": 12.5},
        expected=12.0,
        msg="12.5 rounds half-to-even down to 12.0",
    ),
    ExpressionTestCase(
        "round_to_even_13_5",
        expression={"$round": 13.5},
        expected=14.0,
        msg="13.5 rounds half-to-even up to 14.0",
    ),
    ExpressionTestCase(
        "double_half",
        expression={"$round": DOUBLE_HALF},
        expected=0.0,
        msg="0.5 rounds half-to-even down to 0.0 (0 is even)",
    ),
    ExpressionTestCase(
        "double_two_and_half",
        expression={"$round": DOUBLE_TWO_AND_HALF},
        expected=2.0,
        msg="2.5 rounds half-to-even down to 2.0 (2 is even)",
    ),
    ExpressionTestCase(
        "decimal_round_to_even_10_5",
        expression={"$round": Decimal128("10.5")},
        expected=Decimal128("10"),
        msg="decimal 10.5 rounds half-to-even down to 10",
    ),
    ExpressionTestCase(
        "decimal_round_to_even_11_5",
        expression={"$round": Decimal128("11.5")},
        expected=Decimal128("12"),
        msg="decimal 11.5 rounds half-to-even up to 12",
    ),
]

ROUND_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_positive",
        expression={"$round": "$value"},
        doc={"value": 1},
        expected=1,
        msg="int32 1 is already integral and is returned unchanged",
    ),
    ExpressionTestCase(
        "int64_negative",
        expression={"$round": "$value"},
        doc={"value": Int64(-1)},
        expected=Int64(-1),
        msg="int64 -1 is already integral and is returned unchanged",
    ),
    ExpressionTestCase(
        "double_positive",
        expression={"$round": "$value"},
        doc={"value": 1.5},
        expected=2.0,
        msg="double 1.5 rounds half-to-even up to 2.0",
    ),
    ExpressionTestCase(
        "decimal_positive",
        expression={"$round": "$value"},
        doc={"value": Decimal128("1.5")},
        expected=Decimal128("2"),
        msg="decimal 1.5 rounds half-to-even up to 2",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ROUND_LITERAL_TESTS))
def test_round_literal(collection, test):
    """Test $round with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ROUND_INSERT_TESTS))
def test_round_insert(collection, test):
    """Test $round with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
