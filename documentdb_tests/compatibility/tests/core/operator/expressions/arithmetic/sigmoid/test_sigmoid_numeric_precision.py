"""
arithmetic $sigmoid tests.

Precision and special-value matrix for $sigmoid using both literal (inline)
and inserted document field arguments: decimal128 extremes, half-value
precision for double and decimal128, and Infinity/NaN/null/missing handling.
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
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
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
    MISSING,
)

SIGMOID_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_max",
        expression={"$sigmoid": DECIMAL128_MAX},
        expected=Decimal128("1"),
        msg="decimal128 max saturates to 1",
    ),
    ExpressionTestCase(
        "decimal128_min",
        expression={"$sigmoid": DECIMAL128_MIN},
        expected=Decimal128("0E-6176"),
        msg="decimal128 min saturates to 0E-6176",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        expression={"$sigmoid": DECIMAL128_SMALL_EXPONENT},
        expected=Decimal128("0.5"),
        msg="tiny decimal (1E-6143) ~= 0, sigmoid = 0.5",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        expression={"$sigmoid": DECIMAL128_LARGE_EXPONENT},
        expected=Decimal128("1"),
        msg="huge decimal (1E+6144) saturates to 1",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        expression={"$sigmoid": DECIMAL128_TRAILING_ZERO},
        expected=Decimal128("0.7310585786300048792511592418218362"),
        msg="decimal 1.0 -> sigmoid(1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        expression={"$sigmoid": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=Decimal128("0.7310585786300048792511592418218362"),
        msg="decimal 1.000... -> sigmoid(1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "double_half",
        expression={"$sigmoid": DOUBLE_HALF},
        expected=pytest.approx(0.6224593312018546),
        msg="sigmoid(0.5) ~= 0.62246",
    ),
    ExpressionTestCase(
        "double_one_and_half",
        expression={"$sigmoid": DOUBLE_ONE_AND_HALF},
        expected=pytest.approx(0.8175744761936437),
        msg="sigmoid(1.5) ~= 0.81757",
    ),
    ExpressionTestCase(
        "double_two_and_half",
        expression={"$sigmoid": DOUBLE_TWO_AND_HALF},
        expected=pytest.approx(0.9241418199787566),
        msg="sigmoid(2.5) ~= 0.92414",
    ),
    ExpressionTestCase(
        "double_negative_half",
        expression={"$sigmoid": DOUBLE_NEGATIVE_HALF},
        expected=pytest.approx(0.3775406687981454),
        msg="sigmoid(-0.5) ~= 0.37754",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half",
        expression={"$sigmoid": DOUBLE_NEGATIVE_ONE_AND_HALF},
        expected=pytest.approx(0.18242552380635635),
        msg="sigmoid(-1.5) ~= 0.18243",
    ),
    ExpressionTestCase(
        "double_just_below_half",
        expression={"$sigmoid": DOUBLE_JUST_BELOW_HALF},
        expected=pytest.approx(0.6224593312018546),
        msg="double just below 0.5 rounds to sigmoid(0.5) ~= 0.62246",
    ),
    ExpressionTestCase(
        "double_just_above_half",
        expression={"$sigmoid": DOUBLE_JUST_ABOVE_HALF},
        expected=pytest.approx(0.6224593314368583),
        msg="double just above 0.5 ~= 0.62246 (differs from sigmoid(0.5) past double precision)",
    ),
    ExpressionTestCase(
        "decimal_half",
        expression={"$sigmoid": DECIMAL128_HALF},
        expected=Decimal128("0.6224593312018545646389005657455087"),
        msg="sigmoid(decimal 0.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_one_and_half",
        expression={"$sigmoid": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("0.8175744761936436596072171786562486"),
        msg="sigmoid(decimal 1.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_two_and_half",
        expression={"$sigmoid": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("0.9241418199787564488066938233537521"),
        msg="sigmoid(decimal 2.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_negative_half",
        expression={"$sigmoid": DECIMAL128_NEGATIVE_HALF},
        expected=Decimal128("0.3775406687981454353610994342544915"),
        msg="sigmoid(decimal -0.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half",
        expression={"$sigmoid": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=Decimal128("0.1824255238063563403927828213437517"),
        msg="sigmoid(decimal -1.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_just_below_half",
        expression={"$sigmoid": DECIMAL128_JUST_BELOW_HALF},
        expected=Decimal128("0.6224593312018545646389005657455083"),
        msg="34-digit decimal just below 0.5 (last digit differs from the 0.5 result)",
    ),
    ExpressionTestCase(
        "decimal_just_above_half",
        expression={"$sigmoid": DECIMAL128_JUST_ABOVE_HALF},
        expected=Decimal128("0.6224593312018545646389005657455087"),
        msg="34-digit decimal just above 0.5 (matches the 0.5 result at 34-digit precision)",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$sigmoid": FLOAT_INFINITY},
        expected=1.0,
        msg="sigmoid(+Infinity) = 1.0",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        expression={"$sigmoid": FLOAT_NEGATIVE_INFINITY},
        expected=0.0,
        msg="sigmoid(-Infinity) = 0.0",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={"$sigmoid": DECIMAL128_INFINITY},
        expected=Decimal128("1"),
        msg="sigmoid(decimal +Infinity) = 1",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        expression={"$sigmoid": DECIMAL128_NEGATIVE_INFINITY},
        expected=Decimal128("0E-6176"),
        msg="sigmoid(decimal -Infinity) = 0E-6176",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$sigmoid": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="sigmoid(NaN) = NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$sigmoid": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="sigmoid(decimal NaN) = NaN",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$sigmoid": None},
        expected=None,
        msg="null input returns null",
    ),
    ExpressionTestCase(
        "missing_value",
        expression={"$sigmoid": MISSING},
        expected=None,
        msg="missing input returns null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIGMOID_LITERAL_TESTS))
def test_sigmoid_literal(collection, test):
    """Test $sigmoid with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


SIGMOID_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_max",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_MAX},
        expected=Decimal128("1"),
        msg="decimal128 max saturates to 1",
    ),
    ExpressionTestCase(
        "decimal128_min",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_MIN},
        expected=Decimal128("0E-6176"),
        msg="decimal128 min saturates to 0E-6176",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expected=Decimal128("0.5"),
        msg="tiny decimal (1E-6143) ~= 0, sigmoid = 0.5",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_LARGE_EXPONENT},
        expected=Decimal128("1"),
        msg="huge decimal (1E+6144) saturates to 1",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_TRAILING_ZERO},
        expected=Decimal128("0.7310585786300048792511592418218362"),
        msg="decimal 1.0 -> sigmoid(1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=Decimal128("0.7310585786300048792511592418218362"),
        msg="decimal 1.000... -> sigmoid(1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "double_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DOUBLE_HALF},
        expected=pytest.approx(0.6224593312018546),
        msg="sigmoid(0.5) ~= 0.62246",
    ),
    ExpressionTestCase(
        "double_one_and_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DOUBLE_ONE_AND_HALF},
        expected=pytest.approx(0.8175744761936437),
        msg="sigmoid(1.5) ~= 0.81757",
    ),
    ExpressionTestCase(
        "double_two_and_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DOUBLE_TWO_AND_HALF},
        expected=pytest.approx(0.9241418199787566),
        msg="sigmoid(2.5) ~= 0.92414",
    ),
    ExpressionTestCase(
        "double_negative_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DOUBLE_NEGATIVE_HALF},
        expected=pytest.approx(0.3775406687981454),
        msg="sigmoid(-0.5) ~= 0.37754",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DOUBLE_NEGATIVE_ONE_AND_HALF},
        expected=pytest.approx(0.18242552380635635),
        msg="sigmoid(-1.5) ~= 0.18243",
    ),
    ExpressionTestCase(
        "double_just_below_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DOUBLE_JUST_BELOW_HALF},
        expected=pytest.approx(0.6224593312018546),
        msg="double just below 0.5 rounds to sigmoid(0.5) ~= 0.62246",
    ),
    ExpressionTestCase(
        "decimal_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_HALF},
        expected=Decimal128("0.6224593312018545646389005657455087"),
        msg="sigmoid(decimal 0.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_one_and_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("0.8175744761936436596072171786562486"),
        msg="sigmoid(decimal 1.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_two_and_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("0.9241418199787564488066938233537521"),
        msg="sigmoid(decimal 2.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_negative_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_HALF},
        expected=Decimal128("0.3775406687981454353610994342544915"),
        msg="sigmoid(decimal -0.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=Decimal128("0.1824255238063563403927828213437517"),
        msg="sigmoid(decimal -1.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_just_below_half",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_JUST_BELOW_HALF},
        expected=Decimal128("0.6224593312018545646389005657455083"),
        msg="34-digit decimal just below 0.5 (last digit differs from the 0.5 result)",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$sigmoid": "$value"},
        doc={"value": FLOAT_INFINITY},
        expected=1.0,
        msg="sigmoid(+Infinity) = 1.0",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        expression={"$sigmoid": "$value"},
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        expected=0.0,
        msg="sigmoid(-Infinity) = 0.0",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_INFINITY},
        expected=Decimal128("1"),
        msg="sigmoid(decimal +Infinity) = 1",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        expected=Decimal128("0E-6176"),
        msg="sigmoid(decimal -Infinity) = 0E-6176",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$sigmoid": "$value"},
        doc={"value": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="sigmoid(NaN) = NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$sigmoid": "$value"},
        doc={"value": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="sigmoid(decimal NaN) = NaN",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$sigmoid": "$value"},
        doc={"value": None},
        expected=None,
        msg="null input returns null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIGMOID_INSERT_TESTS))
def test_sigmoid_insert(collection, test):
    """Test $sigmoid with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
