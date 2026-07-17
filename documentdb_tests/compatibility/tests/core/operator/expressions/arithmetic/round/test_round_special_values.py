"""
Half-value and special-value tests for $round expression.

Covers half-boundary precision for double and Decimal128 (including
just-below/just-above-half and negative-zero results), positive/negative
Infinity, NaN, and null.
"""

import math

import pytest
from bson import (
    Decimal128,
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
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

ROUND_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_negative_half",
        expression={"$round": DOUBLE_NEGATIVE_HALF},
        expected=-0.0,
        msg="-0.5 rounds half-to-even to -0.0 (preserves negative-zero sign)",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half",
        expression={"$round": DOUBLE_NEGATIVE_ONE_AND_HALF},
        expected=-2.0,
        msg="-1.5 rounds half-to-even to -2.0",
    ),
    ExpressionTestCase(
        "double_just_below_half",
        expression={"$round": DOUBLE_JUST_BELOW_HALF},
        expected=0.0,
        msg="0.4999999999999994 is below midpoint and rounds down to 0.0",
    ),
    ExpressionTestCase(
        "double_just_above_half",
        expression={"$round": DOUBLE_JUST_ABOVE_HALF},
        expected=1.0,
        msg="0.500000001 is above midpoint and rounds up to 1.0",
    ),
    ExpressionTestCase(
        "decimal_half",
        expression={"$round": DECIMAL128_HALF},
        expected=Decimal128("0"),
        msg="decimal 0.5 rounds half-to-even down to 0",
    ),
    ExpressionTestCase(
        "decimal_one_and_half",
        expression={"$round": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("2"),
        msg="decimal 1.5 rounds half-to-even up to 2",
    ),
    ExpressionTestCase(
        "decimal_two_and_half",
        expression={"$round": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("2"),
        msg="decimal 2.5 rounds half-to-even down to 2",
    ),
    ExpressionTestCase(
        "decimal_negative_half",
        expression={"$round": DECIMAL128_NEGATIVE_HALF},
        expected=Decimal128("-0"),
        msg="decimal -0.5 rounds half-to-even to -0 (preserves negative-zero sign)",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half",
        expression={"$round": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=Decimal128("-2"),
        msg="decimal -1.5 rounds half-to-even to -2",
    ),
    ExpressionTestCase(
        "decimal_just_below_half",
        expression={"$round": DECIMAL128_JUST_BELOW_HALF},
        expected=Decimal128("0"),
        msg="34-digit decimal just below 0.5 rounds down to 0",
    ),
    ExpressionTestCase(
        "decimal_just_above_half",
        expression={"$round": DECIMAL128_JUST_ABOVE_HALF},
        expected=Decimal128("1"),
        msg="34-digit decimal just above 0.5 rounds up to 1",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$round": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="double +Infinity is returned unchanged",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        expression={"$round": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="double -Infinity is returned unchanged",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={"$round": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="decimal128 +Infinity is returned unchanged",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        expression={"$round": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="decimal128 -Infinity is returned unchanged",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$round": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="double NaN rounds to NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$round": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="decimal128 NaN rounds to NaN",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$round": None},
        expected=None,
        msg="null input returns null",
    ),
]

ROUND_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_negative_half",
        expression={"$round": "$value"},
        doc={"value": DOUBLE_NEGATIVE_HALF},
        expected=-0.0,
        msg="-0.5 rounds half-to-even to -0.0 (preserves negative-zero sign)",
    ),
    ExpressionTestCase(
        "decimal_one_and_half",
        expression={"$round": "$value"},
        doc={"value": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("2"),
        msg="decimal 1.5 rounds half-to-even up to 2",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$round": "$value"},
        doc={"value": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="double +Infinity is returned unchanged",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$round": "$value"},
        doc={"value": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="double NaN rounds to NaN",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$round": "$value"},
        doc={"value": None},
        expected=None,
        msg="null input returns null",
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
