"""
Half-value and special value tests for $trunc expression.

Covers half-boundary precision (truncation is not rounding) for double
and Decimal128, Infinity, NaN, and null.
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
    DOUBLE_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_TWO_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

TRUNC_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_half",
        expression={"$trunc": DOUBLE_HALF},
        expected=0.0,
        msg="Should truncate double 0.5 down to 0.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_one_and_half",
        expression={"$trunc": DOUBLE_ONE_AND_HALF},
        expected=1.0,
        msg="Should truncate double 1.5 down to 1.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_two_and_half",
        expression={"$trunc": DOUBLE_TWO_AND_HALF},
        expected=2.0,
        msg="Should truncate double 2.5 down to 2.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_negative_half",
        expression={"$trunc": DOUBLE_NEGATIVE_HALF},
        expected=-0.0,
        msg="Should truncate double -0.5 toward zero to -0.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half",
        expression={"$trunc": DOUBLE_NEGATIVE_ONE_AND_HALF},
        expected=-1.0,
        msg="Should truncate double -1.5 toward zero to -1.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_just_below_half",
        expression={"$trunc": DOUBLE_JUST_BELOW_HALF},
        expected=0.0,
        msg="Should truncate a double just below 0.5 to 0.0",
    ),
    ExpressionTestCase(
        "double_just_above_half",
        expression={"$trunc": DOUBLE_JUST_ABOVE_HALF},
        expected=0.0,
        msg="Should truncate a double just above 0.5 to 0.0",
    ),
    ExpressionTestCase(
        "decimal_half",
        expression={"$trunc": DECIMAL128_HALF},
        expected=Decimal128("0"),
        msg="Should truncate Decimal128 0.5 down to 0 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_one_and_half",
        expression={"$trunc": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("1"),
        msg="Should truncate Decimal128 1.5 down to 1 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_two_and_half",
        expression={"$trunc": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("2"),
        msg="Should truncate Decimal128 2.5 down to 2 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_negative_half",
        expression={"$trunc": DECIMAL128_NEGATIVE_HALF},
        expected=Decimal128("-0"),
        msg="Should truncate Decimal128 -0.5 toward zero to -0 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half",
        expression={"$trunc": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=Decimal128("-1"),
        msg="Should truncate Decimal128 -1.5 toward zero to -1 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_just_below_half",
        expression={"$trunc": DECIMAL128_JUST_BELOW_HALF},
        expected=Decimal128("0"),
        msg="Should truncate a Decimal128 just below 0.5 to 0",
    ),
    ExpressionTestCase(
        "decimal_just_above_half",
        expression={"$trunc": DECIMAL128_JUST_ABOVE_HALF},
        expected=Decimal128("0"),
        msg="Should truncate a Decimal128 just above 0.5 to 0",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$trunc": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="Should preserve positive Infinity unchanged",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        expression={"$trunc": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should preserve negative Infinity unchanged",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={"$trunc": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="Should preserve Decimal128 positive Infinity unchanged",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        expression={"$trunc": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should preserve Decimal128 negative Infinity unchanged",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$trunc": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should propagate float NaN unchanged",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$trunc": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should propagate Decimal128 NaN unchanged",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$trunc": None},
        expected=None,
        msg="Should return null for null input",
    ),
]

TRUNC_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_half",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_HALF},
        expected=0.0,
        msg="Should truncate double 0.5 down to 0.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_one_and_half",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_ONE_AND_HALF},
        expected=1.0,
        msg="Should truncate double 1.5 down to 1.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_two_and_half",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_TWO_AND_HALF},
        expected=2.0,
        msg="Should truncate double 2.5 down to 2.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_negative_half",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_NEGATIVE_HALF},
        expected=-0.0,
        msg="Should truncate double -0.5 toward zero to -0.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_NEGATIVE_ONE_AND_HALF},
        expected=-1.0,
        msg="Should truncate double -1.5 toward zero to -1.0 (no rounding)",
    ),
    ExpressionTestCase(
        "double_just_below_half",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_JUST_BELOW_HALF},
        expected=0.0,
        msg="Should truncate a double just below 0.5 to 0.0",
    ),
    ExpressionTestCase(
        "double_just_above_half",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_JUST_ABOVE_HALF},
        expected=0.0,
        msg="Should truncate a double just above 0.5 to 0.0",
    ),
    ExpressionTestCase(
        "decimal_half",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_HALF},
        expected=Decimal128("0"),
        msg="Should truncate Decimal128 0.5 down to 0 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_one_and_half",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("1"),
        msg="Should truncate Decimal128 1.5 down to 1 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_two_and_half",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("2"),
        msg="Should truncate Decimal128 2.5 down to 2 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_negative_half",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_HALF},
        expected=Decimal128("-0"),
        msg="Should truncate Decimal128 -0.5 toward zero to -0 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=Decimal128("-1"),
        msg="Should truncate Decimal128 -1.5 toward zero to -1 (no rounding)",
    ),
    ExpressionTestCase(
        "decimal_just_below_half",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_JUST_BELOW_HALF},
        expected=Decimal128("0"),
        msg="Should truncate a Decimal128 just below 0.5 to 0",
    ),
    ExpressionTestCase(
        "decimal_just_above_half",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_JUST_ABOVE_HALF},
        expected=Decimal128("0"),
        msg="Should truncate a Decimal128 just above 0.5 to 0",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$trunc": "$value"},
        doc={"value": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="Should preserve positive Infinity unchanged",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        expression={"$trunc": "$value"},
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should preserve negative Infinity unchanged",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="Should preserve Decimal128 positive Infinity unchanged",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should preserve Decimal128 negative Infinity unchanged",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$trunc": "$value"},
        doc={"value": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should propagate float NaN unchanged",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should propagate Decimal128 NaN unchanged",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$trunc": "$value"},
        doc={"value": None},
        expected=None,
        msg="Should return null for null input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TRUNC_LITERAL_TESTS))
def test_trunc_literal(collection, test):
    """Test $trunc with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TRUNC_INSERT_TESTS))
def test_trunc_insert(collection, test):
    """Test $trunc with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
