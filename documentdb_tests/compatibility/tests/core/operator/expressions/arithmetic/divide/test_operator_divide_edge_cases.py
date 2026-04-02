"""Tests for $divide operator — edge cases.

Covers null/missing, NaN, infinity, negative zero, division by zero,
boundary values, precision, and overflow/underflow.
"""

import math
from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import DIVIDE_BY_ZERO_ERROR
from documentdb_tests.framework.test_case import BaseTestCase, pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)


@dataclass(frozen=True)
class DivideTest(BaseTestCase):
    """Test case for $divide operator."""

    dividend: Any = None
    divisor: Any = None


# --- Null handling ---
NULL_TESTS: list[DivideTest] = [
    DivideTest(
        "null_dividend", dividend=None, divisor=2, expected=None, msg="null / number → null"
    ),
    DivideTest(
        "null_divisor", dividend=10, divisor=None, expected=None, msg="number / null → null"
    ),
    DivideTest("both_null", dividend=None, divisor=None, expected=None, msg="null / null → null"),
]

# --- NaN handling ---
NAN_TESTS: list[DivideTest] = [
    DivideTest(
        "nan_dividend",
        dividend=FLOAT_NAN,
        divisor=2,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="NaN / number → NaN",
    ),
    DivideTest(
        "nan_divisor",
        dividend=10,
        divisor=FLOAT_NAN,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="number / NaN → NaN",
    ),
    DivideTest(
        "both_nan",
        dividend=FLOAT_NAN,
        divisor=FLOAT_NAN,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="NaN / NaN → NaN",
    ),
    DivideTest(
        "dec_nan_dividend",
        dividend=DECIMAL128_NAN,
        divisor=2,
        expected=DECIMAL128_NAN,
        msg="Decimal NaN / number → Decimal NaN",
    ),
    DivideTest(
        "dec_nan_divisor",
        dividend=10,
        divisor=DECIMAL128_NAN,
        expected=DECIMAL128_NAN,
        msg="number / Decimal NaN → Decimal NaN",
    ),
    DivideTest(
        "inf_div_inf",
        dividend=FLOAT_INFINITY,
        divisor=FLOAT_INFINITY,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Infinity / Infinity → NaN",
    ),
]

# --- Infinity handling ---
INFINITY_TESTS: list[DivideTest] = [
    DivideTest(
        "inf_dividend",
        dividend=FLOAT_INFINITY,
        divisor=2,
        expected=FLOAT_INFINITY,
        msg="Infinity / number → Infinity",
    ),
    DivideTest(
        "inf_divisor",
        dividend=10,
        divisor=FLOAT_INFINITY,
        expected=0.0,
        msg="number / Infinity → 0",
    ),
    DivideTest(
        "neg_inf_dividend",
        dividend=FLOAT_NEGATIVE_INFINITY,
        divisor=2,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="-Infinity / positive → -Infinity",
    ),
    DivideTest(
        "neg_inf_divisor",
        dividend=10,
        divisor=FLOAT_NEGATIVE_INFINITY,
        expected=-0.0,
        msg="number / -Infinity → -0.0",
    ),
    DivideTest(
        "neg_inf_div_neg",
        dividend=FLOAT_NEGATIVE_INFINITY,
        divisor=-2,
        expected=FLOAT_INFINITY,
        msg="-Infinity / negative → Infinity",
    ),
    DivideTest(
        "dec_inf_dividend",
        dividend=DECIMAL128_INFINITY,
        divisor=2,
        expected=DECIMAL128_INFINITY,
        msg="Decimal Inf / number → Decimal Inf",
    ),
    DivideTest(
        "dec_neg_inf_dividend",
        dividend=DECIMAL128_NEGATIVE_INFINITY,
        divisor=2,
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Decimal -Inf / number → Decimal -Inf",
    ),
    DivideTest(
        "dec_neg_inf_div_neg",
        dividend=DECIMAL128_NEGATIVE_INFINITY,
        divisor=Decimal128("-2"),
        expected=DECIMAL128_INFINITY,
        msg="Decimal -Inf / negative → Decimal Inf",
    ),
]

# --- Negative zero ---
NEGATIVE_ZERO_TESTS: list[DivideTest] = [
    DivideTest(
        "neg_zero_dividend", dividend=-0.0, divisor=1, expected=-0.0, msg="-0.0 / positive → -0.0"
    ),
    DivideTest(
        "neg_zero_div_neg", dividend=-0.0, divisor=-1, expected=0.0, msg="-0.0 / negative → 0.0"
    ),
    DivideTest(
        "zero_div_neg", dividend=0.0, divisor=-1, expected=-0.0, msg="0.0 / negative → -0.0"
    ),
]

# --- Division by zero ---
DIVIDE_BY_ZERO_TESTS: list[DivideTest] = [
    DivideTest(
        "int_div_zero",
        dividend=10,
        divisor=0,
        error_code=DIVIDE_BY_ZERO_ERROR,
        msg="int / 0 → error",
    ),
    DivideTest(
        "double_div_zero",
        dividend=10.0,
        divisor=0.0,
        error_code=DIVIDE_BY_ZERO_ERROR,
        msg="double / 0.0 → error",
    ),
    DivideTest(
        "dec_div_zero",
        dividend=Decimal128("10"),
        divisor=Decimal128("0"),
        error_code=DIVIDE_BY_ZERO_ERROR,
        msg="decimal / 0 → error",
    ),
    DivideTest(
        "zero_div_zero", dividend=0, divisor=0, error_code=DIVIDE_BY_ZERO_ERROR, msg="0 / 0 → error"
    ),
    DivideTest(
        "zero_dbl_div_zero",
        dividend=0.0,
        divisor=0.0,
        error_code=DIVIDE_BY_ZERO_ERROR,
        msg="0.0 / 0.0 → error",
    ),
    DivideTest(
        "dec_zero_div_zero",
        dividend=Decimal128("0"),
        divisor=Decimal128("0"),
        error_code=DIVIDE_BY_ZERO_ERROR,
        msg="decimal 0/0 → error",
    ),
]

# --- Boundary values ---
BOUNDARY_TESTS: list[DivideTest] = [
    DivideTest(
        "int32_max", dividend=INT32_MAX, divisor=10, expected=214748364.7, msg="INT32_MAX / 10"
    ),
    DivideTest(
        "int32_max_m1",
        dividend=INT32_MAX_MINUS_1,
        divisor=10,
        expected=214748364.6,
        msg="INT32_MAX-1 / 10",
    ),
    DivideTest(
        "int32_min", dividend=INT32_MIN, divisor=10, expected=-214748364.8, msg="INT32_MIN / 10"
    ),
    DivideTest(
        "int32_min_p1",
        dividend=INT32_MIN_PLUS_1,
        divisor=10,
        expected=-214748364.7,
        msg="INT32_MIN+1 / 10",
    ),
    DivideTest(
        "int32_self",
        dividend=INT32_MAX,
        divisor=INT32_MAX,
        expected=1.0,
        msg="INT32_MAX / INT32_MAX → 1.0",
    ),
    DivideTest(
        "int64_max",
        dividend=INT64_MAX,
        divisor=Int64(10),
        expected=pytest.approx(9.223372036854776e17),
        msg="INT64_MAX / 10",
    ),
    DivideTest(
        "int64_max_m1",
        dividend=INT64_MAX_MINUS_1,
        divisor=Int64(10),
        expected=pytest.approx(9.223372036854776e17),
        msg="INT64_MAX-1 / 10",
    ),
    DivideTest(
        "int64_min",
        dividend=INT64_MIN,
        divisor=Int64(10),
        expected=pytest.approx(-9.223372036854776e17),
        msg="INT64_MIN / 10",
    ),
    DivideTest(
        "int64_min_p1",
        dividend=INT64_MIN_PLUS_1,
        divisor=Int64(10),
        expected=pytest.approx(-9.223372036854776e17),
        msg="INT64_MIN+1 / 10",
    ),
    DivideTest(
        "int64_self",
        dividend=INT64_MAX,
        divisor=INT64_MAX,
        expected=1.0,
        msg="INT64_MAX / INT64_MAX → 1.0",
    ),
    DivideTest(
        "dbl_subnormal",
        dividend=DOUBLE_MIN_SUBNORMAL,
        divisor=2,
        expected=pytest.approx(2.5e-324),
        msg="Smallest subnormal / 2",
    ),
    DivideTest(
        "dbl_near_min_divisor",
        dividend=1,
        divisor=DOUBLE_NEAR_MIN,
        expected=pytest.approx(1e308),
        msg="1 / near-min double",
    ),
    DivideTest(
        "dbl_near_max",
        dividend=DOUBLE_NEAR_MAX,
        divisor=2,
        expected=pytest.approx(5e307),
        msg="Near-max double / 2",
    ),
    DivideTest(
        "dbl_max_safe_int",
        dividend=DOUBLE_MAX_SAFE_INTEGER,
        divisor=2,
        expected=4503599627370496.0,
        msg="MAX_SAFE_INTEGER / 2",
    ),
    DivideTest(
        "dec_max",
        dividend=DECIMAL128_MAX,
        divisor=Decimal128("2"),
        expected=Decimal128("5.000000000000000000000000000000000E+6144"),
        msg="DECIMAL128_MAX / 2",
    ),
    DivideTest(
        "dec_min",
        dividend=DECIMAL128_MIN,
        divisor=Decimal128("2"),
        expected=Decimal128("-5.000000000000000000000000000000000E+6144"),
        msg="DECIMAL128_MIN / 2",
    ),
    DivideTest(
        "dec_small_exp",
        dividend=DECIMAL128_SMALL_EXPONENT,
        divisor=Decimal128("2"),
        expected=Decimal128("5E-6144"),
        msg="Small exponent decimal / 2",
    ),
]

# --- Precision ---
PRECISION_TESTS: list[DivideTest] = [
    DivideTest(
        "hundred_div_seven",
        dividend=100,
        divisor=7,
        expected=pytest.approx(14.285714285714286),
        msg="100/7 repeating",
    ),
    DivideTest(
        "million_div_seven",
        dividend=1000000,
        divisor=7,
        expected=pytest.approx(142857.14285714286),
        msg="Large dividend repeating",
    ),
    DivideTest(
        "tiny_divisor",
        dividend=1,
        divisor=1e-100,
        expected=1e100,
        msg="Tiny divisor → large result",
    ),
    DivideTest(
        "dec_10_3",
        dividend=Decimal128("10"),
        divisor=Decimal128("3"),
        expected=Decimal128("3.333333333333333333333333333333333"),
        msg="Decimal 10/3 full precision",
    ),
    DivideTest(
        "dec_100_7",
        dividend=Decimal128("100"),
        divisor=Decimal128("7"),
        expected=Decimal128("14.28571428571428571428571428571429"),
        msg="Decimal 100/7 full precision",
    ),
    DivideTest("dbl_half", dividend=DOUBLE_HALF, divisor=2, expected=0.25, msg="0.5 / 2 → 0.25"),
    DivideTest(
        "dbl_one_half", dividend=DOUBLE_ONE_AND_HALF, divisor=3, expected=0.5, msg="1.5 / 3 → 0.5"
    ),
    DivideTest(
        "dbl_just_below",
        dividend=DOUBLE_JUST_BELOW_HALF,
        divisor=2,
        expected=pytest.approx(0.2499999999999997),
        msg="Just below 0.5 / 2",
    ),
    DivideTest(
        "dbl_just_above",
        dividend=DOUBLE_JUST_ABOVE_HALF,
        divisor=2,
        expected=pytest.approx(0.2500000005),
        msg="Just above 0.5 / 2",
    ),
    DivideTest(
        "dec_half",
        dividend=DECIMAL128_HALF,
        divisor=Decimal128("2"),
        expected=Decimal128("0.25"),
        msg="Decimal 0.5 / 2",
    ),
    DivideTest(
        "dec_just_below",
        dividend=DECIMAL128_JUST_BELOW_HALF,
        divisor=Decimal128("2"),
        expected=Decimal128("0.2500000000000000000000000000000000"),
        msg="Decimal just below 0.5 / 2",
    ),
    DivideTest(
        "dec_just_above",
        dividend=DECIMAL128_JUST_ABOVE_HALF,
        divisor=Decimal128("2"),
        expected=Decimal128("0.2500000000000000000000000000000000"),
        msg="Decimal just above 0.5 / 2",
    ),
]

# --- Overflow / underflow ---
OVERFLOW_TESTS: list[DivideTest] = [
    DivideTest(
        "overflow_to_inf",
        dividend=DOUBLE_NEAR_MAX,
        divisor=DOUBLE_MIN_SUBNORMAL,
        expected=FLOAT_INFINITY,
        msg="Near-max / subnormal → Infinity",
    ),
    DivideTest(
        "underflow_to_zero",
        dividend=DOUBLE_MIN_SUBNORMAL,
        divisor=DOUBLE_NEAR_MAX,
        expected=pytest.approx(0.0),
        msg="Subnormal / near-max → 0",
    ),
]

ALL_TESTS = (
    NULL_TESTS
    + NAN_TESTS
    + INFINITY_TESTS
    + NEGATIVE_ZERO_TESTS
    + DIVIDE_BY_ZERO_TESTS
    + BOUNDARY_TESTS
    + PRECISION_TESTS
    + OVERFLOW_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_divide_edge_cases(collection, test):
    """Test $divide operator edge cases."""
    result = execute_expression_with_insert(
        collection,
        {"$divide": ["$dividend", "$divisor"]},
        {"dividend": test.dividend, "divisor": test.divisor},
    )
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)


# --- $missing field behavior (separate — no dividend/divisor fields) ---


MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_dividend",
        expression={"$divide": ["$dividend", "$divisor"]},
        doc={"divisor": 2},
        expected=None,
        msg="missing dividend → null",
    ),
    ExpressionTestCase(
        "missing_divisor",
        expression={"$divide": ["$dividend", "$divisor"]},
        doc={"dividend": 10},
        expected=None,
        msg="missing divisor → null",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$divide": ["$dividend", "$divisor"]},
        doc={},
        expected=None,
        msg="both missing → null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MISSING_TESTS))
def test_divide_missing_field(collection, test):
    """Test $divide with missing fields."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertResult(result, expected=test.expected, msg=test.msg)
