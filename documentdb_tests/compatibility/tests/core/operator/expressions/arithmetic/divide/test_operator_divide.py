import math
from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.test_case import BaseTestCase
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
    MISSING,
)


@dataclass(frozen=True)
class DivideTest(BaseTestCase):
    """Test case for $divide operator."""

    dividend: Any = None
    divisor: Any = None


DIVIDE_TESTS: list[DivideTest] = [
    # Same type operations
    DivideTest(
        "same_type_int32", dividend=10, divisor=2, expected=5.0, msg="Should divide int32 values"
    ),
    DivideTest(
        "same_type_int64",
        dividend=Int64(10),
        divisor=Int64(2),
        expected=5.0,
        msg="Should divide int64 values",
    ),
    DivideTest(
        "same_type_double",
        dividend=10.0,
        divisor=2.0,
        expected=5.0,
        msg="Should divide double values",
    ),
    DivideTest(
        "same_type_decimal",
        dividend=Decimal128("10"),
        divisor=Decimal128("2"),
        expected=Decimal128("5"),
        msg="Should divide decimal128 values",
    ),
    # Mixed numeric types
    DivideTest(
        "int32_int64",
        dividend=10,
        divisor=Int64(2),
        expected=5.0,
        msg="Should divide int32 by int64",
    ),
    DivideTest(
        "int32_double", dividend=10, divisor=2.0, expected=5.0, msg="Should divide int32 by double"
    ),
    DivideTest(
        "int32_decimal",
        dividend=10,
        divisor=Decimal128("2"),
        expected=Decimal128("5"),
        msg="Should divide int32 by decimal128",
    ),
    DivideTest(
        "int64_double",
        dividend=Int64(10),
        divisor=2.0,
        expected=5.0,
        msg="Should divide int64 by double",
    ),
    DivideTest(
        "int64_decimal",
        dividend=Int64(10),
        divisor=Decimal128("2"),
        expected=Decimal128("5"),
        msg="Should divide int64 by decimal128",
    ),
    DivideTest(
        "double_decimal",
        dividend=10.0,
        divisor=Decimal128("2"),
        expected=Decimal128("5.0000000000000"),
        msg="Should divide double by decimal128",
    ),
    # Basic division operations
    DivideTest(
        "evenly_divisible",
        dividend=20,
        divisor=4,
        expected=5.0,
        msg="Should return exact result for even division",
    ),
    DivideTest(
        "repeating_decimal",
        dividend=10,
        divisor=3,
        expected=pytest.approx(3.333333333333333),
        msg="Should return repeating decimal",
    ),
    DivideTest(
        "hundred_div_seven",
        dividend=100,
        divisor=7,
        expected=pytest.approx(14.285714285714286),
        msg="Should return repeating decimal for 100/7",
    ),
    DivideTest(
        "one_div_two", dividend=1, divisor=2, expected=0.5, msg="Should return fractional result"
    ),
    DivideTest(
        "smaller_dividend",
        dividend=5,
        divisor=10,
        expected=0.5,
        msg="Should return fraction when dividend < divisor",
    ),
    DivideTest(
        "one_div_ten", dividend=1, divisor=10, expected=0.1, msg="Should return 0.1 for 1/10"
    ),
    # Negative numbers
    DivideTest(
        "negative_dividend",
        dividend=-10,
        divisor=2,
        expected=-5.0,
        msg="Should return negative when dividend is negative",
    ),
    DivideTest(
        "negative_divisor",
        dividend=10,
        divisor=-2,
        expected=-5.0,
        msg="Should return negative when divisor is negative",
    ),
    DivideTest(
        "both_negative",
        dividend=-10,
        divisor=-2,
        expected=5.0,
        msg="Should return positive when both are negative",
    ),
    DivideTest(
        "negative_seventeen",
        dividend=-17,
        divisor=5,
        expected=-3.4,
        msg="Should handle negative non-even division",
    ),
    DivideTest(
        "negative_one_div_two",
        dividend=-1,
        divisor=2,
        expected=-0.5,
        msg="Should return negative fraction",
    ),
    # Zero dividend
    DivideTest(
        "zero_dividend",
        dividend=0,
        divisor=5,
        expected=0.0,
        msg="Should return 0 when dividend is zero",
    ),
    DivideTest(
        "zero_dividend_negative_divisor",
        dividend=0,
        divisor=-5,
        expected=-0.0,
        msg="Should return -0.0 for 0 divided by negative",
    ),
    DivideTest(
        "zero_double",
        dividend=0.0,
        divisor=3.0,
        expected=0.0,
        msg="Should return 0.0 for double zero dividend",
    ),
    # Fractional operations
    DivideTest(
        "fractional_dividend",
        dividend=10.5,
        divisor=3.0,
        expected=3.5,
        msg="Should handle fractional dividend",
    ),
    DivideTest(
        "fractional_divisor",
        dividend=10.0,
        divisor=2.5,
        expected=4.0,
        msg="Should handle fractional divisor",
    ),
    DivideTest(
        "both_fractional",
        dividend=10.5,
        divisor=2.5,
        expected=4.2,
        msg="Should handle both fractional operands",
    ),
    DivideTest(
        "small_fractional",
        dividend=5.5,
        divisor=2.2,
        expected=2.5,
        msg="Should handle small fractional operands",
    ),
    # Constant-based boundary tests
    # Int32 boundaries
    DivideTest(
        "int32_max_dividend",
        dividend=INT32_MAX,
        divisor=10,
        expected=214748364.7,
        msg="Should handle INT32_MAX as dividend",
    ),
    DivideTest(
        "int32_max_minus_1_dividend",
        dividend=INT32_MAX_MINUS_1,
        divisor=10,
        expected=214748364.6,
        msg="Should handle INT32_MAX-1 as dividend",
    ),
    DivideTest(
        "int32_min_dividend",
        dividend=INT32_MIN,
        divisor=10,
        expected=-214748364.8,
        msg="Should handle INT32_MIN as dividend",
    ),
    DivideTest(
        "int32_min_plus_1_dividend",
        dividend=INT32_MIN_PLUS_1,
        divisor=10,
        expected=-214748364.7,
        msg="Should handle INT32_MIN+1 as dividend",
    ),
    # Int64 boundaries
    DivideTest(
        "int64_max_dividend",
        dividend=INT64_MAX,
        divisor=Int64(10),
        expected=pytest.approx(9.223372036854776e17),
        msg="Should handle INT64_MAX as dividend",
    ),
    DivideTest(
        "int64_max_minus_1_dividend",
        dividend=INT64_MAX_MINUS_1,
        divisor=Int64(10),
        expected=pytest.approx(9.223372036854776e17),
        msg="Should handle INT64_MAX-1 as dividend",
    ),
    DivideTest(
        "int64_min_dividend",
        dividend=INT64_MIN,
        divisor=Int64(10),
        expected=pytest.approx(-9.223372036854776e17),
        msg="Should handle INT64_MIN as dividend",
    ),
    DivideTest(
        "int64_min_plus_1_dividend",
        dividend=INT64_MIN_PLUS_1,
        divisor=Int64(10),
        expected=pytest.approx(-9.223372036854776e17),
        msg="Should handle INT64_MIN+1 as dividend",
    ),
    # Double boundaries
    DivideTest(
        "double_min_subnormal_dividend",
        dividend=DOUBLE_MIN_SUBNORMAL,
        divisor=2,
        expected=pytest.approx(2.5e-324),
        msg="Should handle smallest subnormal double",
    ),
    DivideTest(
        "double_near_min_divisor",
        dividend=1,
        divisor=DOUBLE_NEAR_MIN,
        expected=pytest.approx(1e308),
        msg="Should handle near-min double as divisor",
    ),
    DivideTest(
        "double_near_max_dividend",
        dividend=DOUBLE_NEAR_MAX,
        divisor=2,
        expected=pytest.approx(5e307),
        msg="Should handle near-max double as dividend",
    ),
    DivideTest(
        "double_max_safe_integer",
        dividend=DOUBLE_MAX_SAFE_INTEGER,
        divisor=2,
        expected=4503599627370496.0,
        msg="Should handle max safe integer as dividend",
    ),
    # Decimal128 boundaries
    DivideTest(
        "decimal128_max_dividend",
        dividend=DECIMAL128_MAX,
        divisor=Decimal128("2"),
        expected=Decimal128("5.000000000000000000000000000000000E+6144"),
        msg="Should handle DECIMAL128_MAX as dividend",
    ),
    DivideTest(
        "decimal128_min_dividend",
        dividend=DECIMAL128_MIN,
        divisor=Decimal128("2"),
        expected=Decimal128("-5.000000000000000000000000000000000E+6144"),
        msg="Should handle DECIMAL128_MIN as dividend",
    ),
    DivideTest(
        "decimal128_small_exponent",
        dividend=DECIMAL128_SMALL_EXPONENT,
        divisor=Decimal128("2"),
        expected=Decimal128("5E-6144"),
        msg="Should handle small exponent decimal128",
    ),
    # Infinity constants
    DivideTest(
        "float_inf_dividend",
        dividend=FLOAT_INFINITY,
        divisor=2,
        expected=FLOAT_INFINITY,
        msg="Should return infinity when dividing infinity",
    ),
    DivideTest(
        "float_inf_divisor",
        dividend=10,
        divisor=FLOAT_INFINITY,
        expected=0.0,
        msg="Should return 0 when dividing by infinity",
    ),
    DivideTest(
        "float_neg_inf_dividend",
        dividend=FLOAT_NEGATIVE_INFINITY,
        divisor=2,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -infinity when dividing -infinity",
    ),
    DivideTest(
        "float_neg_inf_divisor",
        dividend=10,
        divisor=FLOAT_NEGATIVE_INFINITY,
        expected=-0.0,
        msg="Should return -0.0 when dividing by -infinity",
    ),
    DivideTest(
        "neg_inf_dividend_neg_divisor",
        dividend=FLOAT_NEGATIVE_INFINITY,
        divisor=-2,
        expected=FLOAT_INFINITY,
        msg="Should return +infinity for -inf/-2",
    ),
    DivideTest(
        "decimal128_inf_dividend",
        dividend=DECIMAL128_INFINITY,
        divisor=2,
        expected=DECIMAL128_INFINITY,
        msg="Should return decimal infinity when dividing decimal infinity",
    ),
    DivideTest(
        "decimal128_neg_inf_dividend",
        dividend=DECIMAL128_NEGATIVE_INFINITY,
        divisor=2,
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should return decimal -infinity when dividing decimal -infinity",
    ),
    DivideTest(
        "decimal_neg_inf_dividend_neg_divisor",
        dividend=DECIMAL128_NEGATIVE_INFINITY,
        divisor=Decimal128("-2"),
        expected=DECIMAL128_INFINITY,
        msg="Should return decimal +infinity for -inf/-2",
    ),
    # NaN constants
    DivideTest(
        "float_nan_dividend",
        dividend=FLOAT_NAN,
        divisor=2,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when dividend is NaN",
    ),
    DivideTest(
        "float_nan_divisor",
        dividend=10,
        divisor=FLOAT_NAN,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when divisor is NaN",
    ),
    DivideTest(
        "both_nan",
        dividend=FLOAT_NAN,
        divisor=FLOAT_NAN,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when both are NaN",
    ),
    DivideTest(
        "inf_div_inf",
        dividend=FLOAT_INFINITY,
        divisor=FLOAT_INFINITY,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity/infinity",
    ),
    DivideTest(
        "decimal128_nan_dividend",
        dividend=DECIMAL128_NAN,
        divisor=2,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when dividend is decimal NaN",
    ),
    DivideTest(
        "decimal128_nan_divisor",
        dividend=10,
        divisor=DECIMAL128_NAN,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when divisor is decimal NaN",
    ),
    # Precision
    DivideTest(
        "decimal_precision",
        dividend=Decimal128("10"),
        divisor=Decimal128("3"),
        expected=Decimal128("3.333333333333333333333333333333333"),
        msg="Should preserve decimal128 precision for 10/3",
    ),
    DivideTest(
        "decimal_precision_complex",
        dividend=Decimal128("100"),
        divisor=Decimal128("7"),
        expected=Decimal128("14.28571428571428571428571428571429"),
        msg="Should preserve decimal128 precision for 100/7",
    ),
    DivideTest(
        "million_div_seven",
        dividend=1000000,
        divisor=7,
        expected=pytest.approx(142857.14285714286),
        msg="Should handle large dividend with repeating result",
    ),
    DivideTest(
        "tiny_divisor",
        dividend=1,
        divisor=DOUBLE_NEAR_MIN,
        expected=pytest.approx(1e308),
        msg="Should handle very small divisor",
    ),
    DivideTest(
        "tiny_divisor_hundred",
        dividend=1,
        divisor=1e-100,
        expected=1e100,
        msg="Should handle tiny divisor producing large result",
    ),
    # Rounding edge cases
    DivideTest(
        "double_half_dividend",
        dividend=DOUBLE_HALF,
        divisor=2,
        expected=0.25,
        msg="Should correctly halve 0.5",
    ),
    DivideTest(
        "double_one_and_half_dividend",
        dividend=DOUBLE_ONE_AND_HALF,
        divisor=3,
        expected=0.5,
        msg="Should correctly divide 1.5 by 3",
    ),
    DivideTest(
        "double_just_below_half_dividend",
        dividend=DOUBLE_JUST_BELOW_HALF,
        divisor=2,
        expected=pytest.approx(0.2499999999999997),
        msg="Should preserve precision near 0.5 boundary",
    ),
    DivideTest(
        "double_just_above_half_dividend",
        dividend=DOUBLE_JUST_ABOVE_HALF,
        divisor=2,
        expected=pytest.approx(0.2500000005),
        msg="Should preserve precision just above 0.5",
    ),
    DivideTest(
        "decimal_half_dividend",
        dividend=DECIMAL128_HALF,
        divisor=Decimal128("2"),
        expected=Decimal128("0.25"),
        msg="Should correctly halve decimal 0.5",
    ),
    DivideTest(
        "decimal_just_below_half_dividend",
        dividend=DECIMAL128_JUST_BELOW_HALF,
        divisor=Decimal128("2"),
        expected=Decimal128("0.2500000000000000000000000000000000"),
        msg="Should preserve decimal precision near 0.5",
    ),
    DivideTest(
        "decimal_just_above_half_dividend",
        dividend=DECIMAL128_JUST_ABOVE_HALF,
        divisor=Decimal128("2"),
        expected=Decimal128("0.2500000000000000000000000000000000"),
        msg="Should preserve decimal precision just above 0.5",
    ),
    # Null and missing (MISSING constant)
    DivideTest(
        "null_divisor",
        dividend=10,
        divisor=None,
        expected=None,
        msg="Should return null when divisor is null",
    ),
    DivideTest(
        "null_dividend",
        dividend=None,
        divisor=2,
        expected=None,
        msg="Should return null when dividend is null",
    ),
    DivideTest(
        "missing_dividend",
        dividend=MISSING,
        divisor=2,
        expected=None,
        msg="Should return null when dividend is missing",
    ),
    DivideTest(
        "missing_divisor",
        dividend=10,
        divisor=MISSING,
        expected=None,
        msg="Should return null when divisor is missing",
    ),
    DivideTest(
        "both_null",
        dividend=None,
        divisor=None,
        expected=None,
        msg="Should return null when both are null",
    ),
    # Error cases - invalid types
    DivideTest(
        "string_divisor",
        dividend=10,
        divisor="string",
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string divisor",
    ),
    DivideTest(
        "string_dividend",
        dividend="string",
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string dividend",
    ),
    DivideTest(
        "boolean_divisor",
        dividend=10,
        divisor=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject boolean divisor",
    ),
    DivideTest(
        "boolean_dividend",
        dividend=True,
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject boolean dividend",
    ),
    DivideTest(
        "array_divisor",
        dividend=10,
        divisor=[2, 3],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array divisor",
    ),
    DivideTest(
        "array_dividend",
        dividend=[2, 3],
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array dividend",
    ),
    DivideTest(
        "object_divisor",
        dividend=10,
        divisor={"a": 2},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object divisor",
    ),
    DivideTest(
        "object_dividend",
        dividend={"a": 2},
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object dividend",
    ),
    DivideTest(
        "empty_array_dividend",
        dividend=[],
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array dividend",
    ),
    DivideTest(
        "empty_object_dividend",
        dividend={},
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object dividend",
    ),
    DivideTest(
        "empty_array_divisor",
        dividend=10,
        divisor=[],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array divisor",
    ),
    DivideTest(
        "empty_object_divisor",
        dividend=10,
        divisor={},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object divisor",
    ),
    # Error cases - zero divisor
    DivideTest(
        "zero_divisor",
        dividend=10,
        divisor=0,
        error_code=BAD_VALUE_ERROR,
        msg="Should reject division by zero int",
    ),
    DivideTest(
        "zero_divisor_double",
        dividend=10,
        divisor=0.0,
        error_code=BAD_VALUE_ERROR,
        msg="Should reject division by zero double",
    ),
    DivideTest(
        "decimal_zero_divisor",
        dividend=Decimal128("10"),
        divisor=Decimal128("0"),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject division by zero decimal128",
    ),
    DivideTest(
        "zero_div_zero",
        dividend=0,
        divisor=0,
        error_code=BAD_VALUE_ERROR,
        msg="Should reject 0/0",
    ),
    DivideTest(
        "zero_double_div_zero",
        dividend=0.0,
        divisor=0.0,
        error_code=BAD_VALUE_ERROR,
        msg="Should reject 0.0/0.0",
    ),
    DivideTest(
        "decimal_zero_div_zero",
        dividend=Decimal128("0"),
        divisor=Decimal128("0"),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject decimal 0/0",
    ),
]


@pytest.mark.parametrize("test", DIVIDE_TESTS, ids=lambda t: t.id)
def test_divide_literal(collection, test):
    """Test $divide from literals"""
    result = execute_expression(collection, {"$divide": [test.dividend, test.divisor]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize(
    "test",
    [t for t in DIVIDE_TESTS if t.dividend != MISSING and t.divisor != MISSING],
    ids=lambda t: t.id,
)
def test_divide_insert(collection, test):
    """Test $divide from documents"""
    result = execute_expression_with_insert(
        collection,
        {"$divide": ["$dividend", "$divisor"]},
        {"dividend": test.dividend, "divisor": test.divisor},
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize(
    "test", [t for t in DIVIDE_TESTS if t.dividend != MISSING], ids=lambda t: t.id
)
def test_divide_mixed(collection, test):
    """Test $divide mixed literal and document"""
    result = execute_expression_with_insert(
        collection, {"$divide": ["$dividend", test.divisor]}, {"dividend": test.dividend}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
