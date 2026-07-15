import math

import pytest
from bson import Decimal128

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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

MULTIPLY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity",
        expression={"$multiply": [FLOAT_INFINITY, 2]},
        expected=float("inf"),
        msg="Should handle infinity",
    ),
    ExpressionTestCase(
        "negative_infinity",
        expression={"$multiply": [FLOAT_NEGATIVE_INFINITY, 2]},
        expected=float("-inf"),
        msg="Should handle negative infinity",
    ),
    ExpressionTestCase(
        "single_infinity",
        expression={"$multiply": [FLOAT_INFINITY]},
        expected=float("inf"),
        msg="Should handle single infinity",
    ),
    ExpressionTestCase(
        "decimal_infinity",
        expression={"$multiply": [DECIMAL128_INFINITY, 2]},
        expected=Decimal128("Infinity"),
        msg="Should handle decimal infinity",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity",
        expression={"$multiply": [DECIMAL128_NEGATIVE_INFINITY, 2]},
        expected=Decimal128("-Infinity"),
        msg="Should handle decimal negative infinity",
    ),
    ExpressionTestCase(
        "inf_times_inf",
        expression={"$multiply": [FLOAT_INFINITY, FLOAT_INFINITY]},
        expected=float("inf"),
        msg="Should handle inf times inf",
    ),
    ExpressionTestCase(
        "neg_inf_times_neg_inf",
        expression={"$multiply": [FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=float("inf"),
        msg="Should handle neg inf times neg inf",
    ),
    ExpressionTestCase(
        "inf_times_negative",
        expression={"$multiply": [FLOAT_INFINITY, -1]},
        expected=float("-inf"),
        msg="Should handle inf times negative",
    ),
    ExpressionTestCase(
        "neg_inf_times_negative",
        expression={"$multiply": [FLOAT_NEGATIVE_INFINITY, -1]},
        expected=float("inf"),
        msg="Should handle neg inf times negative",
    ),
    ExpressionTestCase(
        "nan_multiply_two",
        expression={"$multiply": [FLOAT_NAN, 2]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan multiply two",
    ),
    ExpressionTestCase(
        "inf_times_zero",
        expression={"$multiply": [FLOAT_INFINITY, 0]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle inf times zero",
    ),
    ExpressionTestCase(
        "neg_inf_times_zero",
        expression={"$multiply": [FLOAT_NEGATIVE_INFINITY, 0]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle neg inf times zero",
    ),
    ExpressionTestCase(
        "nan_times_nan",
        expression={"$multiply": [FLOAT_NAN, FLOAT_NAN]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan times nan",
    ),
    ExpressionTestCase(
        "decimal_nan_times_nan",
        expression={"$multiply": [DECIMAL128_NAN, DECIMAL128_NAN]},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan times nan",
    ),
    ExpressionTestCase(
        "nan_times_inf",
        expression={"$multiply": [FLOAT_NAN, FLOAT_INFINITY]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan times inf",
    ),
    ExpressionTestCase(
        "decimal_nan",
        expression={"$multiply": [DECIMAL128_NAN, 2]},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan",
    ),
    ExpressionTestCase(
        "decimal_inf_times_zero",
        expression={"$multiply": [DECIMAL128_INFINITY, 0]},
        expected=DECIMAL128_NAN,
        msg="Should handle decimal inf times zero",
    ),
    ExpressionTestCase(
        "nan_times_zero",
        expression={"$multiply": [FLOAT_NAN, 0]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan times zero",
    ),
]


MULTIPLY_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_INFINITY, "val1": 2},
        expected=float("inf"),
        msg="Should handle infinity",
    ),
    ExpressionTestCase(
        "negative_infinity",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY, "val1": 2},
        expected=float("-inf"),
        msg="Should handle negative infinity",
    ),
    ExpressionTestCase(
        "single_infinity",
        expression={"$multiply": ["$val0"]},
        doc={"val0": FLOAT_INFINITY},
        expected=float("inf"),
        msg="Should handle single infinity",
    ),
    ExpressionTestCase(
        "decimal_infinity",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_INFINITY, "val1": 2},
        expected=Decimal128("Infinity"),
        msg="Should handle decimal infinity",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_NEGATIVE_INFINITY, "val1": 2},
        expected=Decimal128("-Infinity"),
        msg="Should handle decimal negative infinity",
    ),
    ExpressionTestCase(
        "inf_times_inf",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_INFINITY, "val1": FLOAT_INFINITY},
        expected=float("inf"),
        msg="Should handle inf times inf",
    ),
    ExpressionTestCase(
        "neg_inf_times_neg_inf",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY, "val1": FLOAT_NEGATIVE_INFINITY},
        expected=float("inf"),
        msg="Should handle neg inf times neg inf",
    ),
    ExpressionTestCase(
        "inf_times_negative",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_INFINITY, "val1": -1},
        expected=float("-inf"),
        msg="Should handle inf times negative",
    ),
    ExpressionTestCase(
        "neg_inf_times_negative",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY, "val1": -1},
        expected=float("inf"),
        msg="Should handle neg inf times negative",
    ),
    ExpressionTestCase(
        "nan_multiply_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_NAN, "val1": 2},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan multiply two",
    ),
    ExpressionTestCase(
        "inf_times_zero",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_INFINITY, "val1": 0},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle inf times zero",
    ),
    ExpressionTestCase(
        "neg_inf_times_zero",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY, "val1": 0},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle neg inf times zero",
    ),
    ExpressionTestCase(
        "nan_times_nan",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_NAN, "val1": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan times nan",
    ),
    ExpressionTestCase(
        "decimal_nan_times_nan",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_NAN, "val1": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan times nan",
    ),
    ExpressionTestCase(
        "nan_times_inf",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": FLOAT_NAN, "val1": FLOAT_INFINITY},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan times inf",
    ),
    ExpressionTestCase(
        "decimal_nan",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_NAN, "val1": 2},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan",
    ),
    ExpressionTestCase(
        "decimal_inf_times_zero",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_INFINITY, "val1": 0},
        expected=DECIMAL128_NAN,
        msg="Should handle decimal inf times zero",
    ),
]


MULTIPLY_MIXED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": FLOAT_INFINITY},
        expected=float("inf"),
        msg="Should handle infinity",
    ),
    ExpressionTestCase(
        "negative_infinity",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY},
        expected=float("-inf"),
        msg="Should handle negative infinity",
    ),
    ExpressionTestCase(
        "decimal_infinity",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_INFINITY},
        expected=Decimal128("Infinity"),
        msg="Should handle decimal infinity",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_NEGATIVE_INFINITY},
        expected=Decimal128("-Infinity"),
        msg="Should handle decimal negative infinity",
    ),
    ExpressionTestCase(
        "inf_times_inf",
        expression={"$multiply": ["$val0", FLOAT_INFINITY]},
        doc={"val0": FLOAT_INFINITY},
        expected=float("inf"),
        msg="Should handle inf times inf",
    ),
    ExpressionTestCase(
        "neg_inf_times_neg_inf",
        expression={"$multiply": ["$val0", FLOAT_NEGATIVE_INFINITY]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY},
        expected=float("inf"),
        msg="Should handle neg inf times neg inf",
    ),
    ExpressionTestCase(
        "inf_times_negative",
        expression={"$multiply": ["$val0", -1]},
        doc={"val0": FLOAT_INFINITY},
        expected=float("-inf"),
        msg="Should handle inf times negative",
    ),
    ExpressionTestCase(
        "neg_inf_times_negative",
        expression={"$multiply": ["$val0", -1]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY},
        expected=float("inf"),
        msg="Should handle neg inf times negative",
    ),
    ExpressionTestCase(
        "nan_multiply_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan multiply two",
    ),
    ExpressionTestCase(
        "inf_times_zero",
        expression={"$multiply": ["$val0", 0]},
        doc={"val0": FLOAT_INFINITY},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle inf times zero",
    ),
    ExpressionTestCase(
        "neg_inf_times_zero",
        expression={"$multiply": ["$val0", 0]},
        doc={"val0": FLOAT_NEGATIVE_INFINITY},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle neg inf times zero",
    ),
    ExpressionTestCase(
        "nan_times_nan",
        expression={"$multiply": ["$val0", FLOAT_NAN]},
        doc={"val0": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan times nan",
    ),
    ExpressionTestCase(
        "decimal_nan_times_nan",
        expression={"$multiply": ["$val0", DECIMAL128_NAN]},
        doc={"val0": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan times nan",
    ),
    ExpressionTestCase(
        "nan_times_inf",
        expression={"$multiply": ["$val0", FLOAT_INFINITY]},
        doc={"val0": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan times inf",
    ),
    ExpressionTestCase(
        "decimal_nan",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan",
    ),
    ExpressionTestCase(
        "decimal_inf_times_zero",
        expression={"$multiply": ["$val0", 0]},
        doc={"val0": DECIMAL128_INFINITY},
        expected=DECIMAL128_NAN,
        msg="Should handle decimal inf times zero",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_LITERAL_TESTS))
def test_multiply_literal(collection, test):
    """Test $multiply from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_INSERT_TESTS))
def test_multiply_insert(collection, test):
    """Test $multiply from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_MIXED_TESTS))
def test_multiply_mixed(collection, test):
    """Test $multiply mixed literal and document"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
