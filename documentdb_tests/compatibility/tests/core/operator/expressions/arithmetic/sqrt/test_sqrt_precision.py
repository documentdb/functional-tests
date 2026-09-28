"""
arithmetic $sqrt tests.

Tests for the arithmetic $sqrt operator: non-perfect-square values, numeric
boundaries, decimal128 precision, special values (NaN/Infinity/null/missing),
and the single-element array wrapper, as literal expressions and as
inserted document fields (a reduced-but-present subset).
"""

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
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_TWO_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    MISSING,
)

SQRT_PRECISION_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_ten",
        expression={"$sqrt": 10},
        expected=pytest.approx(3.1622776601683795),
        msg="sqrt(10) ~= 3.16228 (irrational)",
    ),
    ExpressionTestCase(
        "int32_thousand",
        expression={"$sqrt": 1000},
        expected=pytest.approx(31.622776601683793),
        msg="sqrt(1000) ~= 31.6228",
    ),
    ExpressionTestCase(
        "double_0_1",
        expression={"$sqrt": 0.1},
        expected=pytest.approx(0.31622776601683794),
        msg="sqrt(0.1) ~= 0.316228",
    ),
    ExpressionTestCase(
        "double_0_001",
        expression={"$sqrt": 0.001},
        expected=pytest.approx(0.03162277660168379),
        msg="sqrt(0.001) ~= 0.0316228",
    ),
    ExpressionTestCase(
        "decimal_ten",
        expression={"$sqrt": Decimal128("10")},
        expected=Decimal128("3.162277660168379331998893544432719"),
        msg="sqrt(decimal 10) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_thousand",
        expression={"$sqrt": Decimal128("1000")},
        expected=Decimal128("31.62277660168379331998893544432719"),
        msg="sqrt(decimal 1000) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_0_1",
        expression={"$sqrt": Decimal128("0.1")},
        expected=Decimal128("0.3162277660168379331998893544432719"),
        msg="sqrt(decimal 0.1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_0_001",
        expression={"$sqrt": Decimal128("0.001")},
        expected=Decimal128("0.03162277660168379331998893544432719"),
        msg="sqrt(decimal 0.001) to 34-digit precision",
    ),
    ExpressionTestCase(
        "double_pi",
        expression={"$sqrt": math.pi},
        expected=pytest.approx(1.7724538509055159),
        msg="sqrt(pi) ~= 1.77245",
    ),
    ExpressionTestCase(
        "double_e",
        expression={"$sqrt": math.e},
        expected=pytest.approx(1.6487212707001282),
        msg="sqrt(e) ~= 1.64872",
    ),
    ExpressionTestCase(
        "int32_max",
        expression={"$sqrt": INT32_MAX},
        expected=pytest.approx(46340.95001),
        msg="sqrt(INT32_MAX) ~= 46340.95",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        expression={"$sqrt": INT32_MAX_MINUS_1},
        expected=pytest.approx(46340.95001),
        msg="sqrt(INT32_MAX-1) ~= 46340.95 (adjacent to max)",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$sqrt": INT64_MAX},
        expected=pytest.approx(3.0370004999760455e9),
        msg="sqrt(INT64_MAX) ~= 3.037e9",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        expression={"$sqrt": INT64_MAX_MINUS_1},
        expected=pytest.approx(3.0370004999760455e9),
        msg="sqrt(INT64_MAX-1) ~= 3.037e9 (adjacent to max)",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$sqrt": DOUBLE_MIN_SUBNORMAL},
        expected=pytest.approx(2.2250738585072014e-162),
        msg="sqrt of smallest subnormal double ~= 2.225e-162",
    ),
    ExpressionTestCase(
        "double_near_min",
        expression={"$sqrt": DOUBLE_NEAR_MIN},
        expected=pytest.approx(3.162277660168379e-154),
        msg="sqrt(1e-308) ~= 3.16e-154",
    ),
    ExpressionTestCase(
        "double_near_max",
        expression={"$sqrt": DOUBLE_NEAR_MAX},
        expected=1e154,
        msg="sqrt(1e308) = 1e154",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        expression={"$sqrt": DOUBLE_MAX_SAFE_INTEGER},
        expected=pytest.approx(94906265.62425156),
        msg="sqrt(2^53) ~= 94906265.6",
    ),
    ExpressionTestCase(
        "decimal128_max",
        expression={"$sqrt": DECIMAL128_MAX},
        expected=Decimal128("3.162277660168379331998893544432718E+3072"),
        msg="sqrt(decimal128 max) ~= 3.16E+3072",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        expression={"$sqrt": DECIMAL128_SMALL_EXPONENT},
        expected=Decimal128("3.162277660168379331998893544432719E-3072"),
        msg="sqrt(1E-6143) ~= 3.16E-3072",
    ),
    ExpressionTestCase(
        "decimal128_min_positive",
        expression={"$sqrt": DECIMAL128_MIN_POSITIVE},
        expected=Decimal128("1E-3088"),
        msg="sqrt(1E-6176) = 1E-3088 (exact, even exponent)",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        expression={"$sqrt": DECIMAL128_LARGE_EXPONENT},
        expected=Decimal128("1.00000000000000000E+3072"),
        msg="sqrt(1E+6144) = 1E+3072",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        expression={"$sqrt": DECIMAL128_TRAILING_ZERO},
        expected=Decimal128("1.0"),
        msg="sqrt(decimal 1.0) = 1.0 (trailing-zero scale preserved)",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        expression={"$sqrt": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=Decimal128("1.0000000000000000"),
        msg="sqrt(decimal 1.000...) preserves the trailing-zero scale",
    ),
    ExpressionTestCase(
        "double_half",
        expression={"$sqrt": DOUBLE_HALF},
        expected=pytest.approx(0.7071067811865476),
        msg="sqrt(0.5) ~= 0.70711",
    ),
    ExpressionTestCase(
        "double_one_and_half",
        expression={"$sqrt": DOUBLE_ONE_AND_HALF},
        expected=pytest.approx(1.224744871391589),
        msg="sqrt(1.5) ~= 1.22474",
    ),
    ExpressionTestCase(
        "double_two_and_half",
        expression={"$sqrt": DOUBLE_TWO_AND_HALF},
        expected=pytest.approx(1.5811388300841898),
        msg="sqrt(2.5) ~= 1.58114",
    ),
    ExpressionTestCase(
        "double_just_below_half",
        expression={"$sqrt": DOUBLE_JUST_BELOW_HALF},
        expected=pytest.approx(0.7071067811865475),
        msg="sqrt of double just below 0.5 ~= 0.70711",
    ),
    ExpressionTestCase(
        "double_just_above_half",
        expression={"$sqrt": DOUBLE_JUST_ABOVE_HALF},
        expected=pytest.approx(0.7071067816840446),
        msg="sqrt of double just above 0.5 ~= 0.70711 (distinct from 0.5)",
    ),
    ExpressionTestCase(
        "decimal_half",
        expression={"$sqrt": DECIMAL128_HALF},
        expected=Decimal128("0.7071067811865475244008443621048490"),
        msg="sqrt(decimal 0.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_one_and_half",
        expression={"$sqrt": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("1.224744871391589049098642037352946"),
        msg="sqrt(decimal 1.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_two_and_half",
        expression={"$sqrt": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("1.581138830084189665999446772216359"),
        msg="sqrt(decimal 2.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "decimal_just_above_half",
        expression={"$sqrt": DECIMAL128_JUST_ABOVE_HALF},
        expected=Decimal128("0.7071067811865475244008443621048491"),
        msg="34-digit decimal just above 0.5 (last digit differs from the 0.5 result)",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$sqrt": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="sqrt(+Infinity) = +Infinity",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={"$sqrt": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="sqrt(decimal +Infinity) = +Infinity",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$sqrt": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for float nan",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$sqrt": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal128 nan",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$sqrt": None},
        expected=None,
        msg="Should return null for null value",
    ),
    ExpressionTestCase(
        "missing_value",
        expression={"$sqrt": MISSING},
        expected=None,
        msg="Should return null for missing value",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$sqrt": [25]},
        expected=5.0,
        msg="Should accept single-element array as implicit scalar unwrap",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SQRT_PRECISION_LITERAL_TESTS))
def test_sqrt_precision_literal(collection, test):
    """Test $sqrt with literal boundary, decimal128-precision, and special values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


SQRT_PRECISION_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_max",
        expression={"$sqrt": "$value"},
        doc={"value": INT64_MAX},
        expected=pytest.approx(3.0370004999760455e9),
        msg="sqrt(INT64_MAX) ~= 3.037e9",
    ),
    ExpressionTestCase(
        "decimal128_max",
        expression={"$sqrt": "$value"},
        doc={"value": DECIMAL128_MAX},
        expected=Decimal128("3.162277660168379331998893544432718E+3072"),
        msg="sqrt(decimal128 max) ~= 3.16E+3072",
    ),
    ExpressionTestCase(
        "decimal_half",
        expression={"$sqrt": "$value"},
        doc={"value": DECIMAL128_HALF},
        expected=Decimal128("0.7071067811865475244008443621048490"),
        msg="sqrt(decimal 0.5) to 34-digit precision",
    ),
    ExpressionTestCase(
        "float_infinity",
        expression={"$sqrt": "$value"},
        doc={"value": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="sqrt(+Infinity) = +Infinity",
    ),
    ExpressionTestCase(
        "float_nan",
        expression={"$sqrt": "$value"},
        doc={"value": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for float nan",
    ),
    ExpressionTestCase(
        "null_value",
        expression={"$sqrt": "$value"},
        doc={"value": None},
        expected=None,
        msg="Should return null for null value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SQRT_PRECISION_INSERT_TESTS))
def test_sqrt_precision_insert(collection, test):
    """Test $sqrt with inserted boundary, decimal128-precision, and special values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
