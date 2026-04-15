from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.avg.utils.avg_common import (  # noqa: E501
    AvgTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_ZERO,
)

# Property [Decimal128 Precision and Boundaries]: Decimal128 preserves full
# 34-digit precision, trailing zeros, and extreme exponent values through
# averaging.
AVG_DECIMAL128_PRECISION_TESTS: list[AvgTest] = [
    AvgTest(
        "dec_precision_34_digit",
        args=[Decimal128("1"), Decimal128("1"), Decimal128("2")],
        expected=Decimal128("1.333333333333333333333333333333333"),
        msg="$avg should preserve full 34-digit Decimal128 precision",
    ),
    AvgTest(
        "dec_precision_trailing_zeros",
        args=[Decimal128("1.00"), Decimal128("2.00")],
        expected=Decimal128("1.50"),
        msg="$avg should preserve trailing zeros based on input precision",
    ),
    AvgTest(
        "dec_precision_max_coefficient_pair",
        args=[Decimal128("9" * 34), Decimal128("9" * 34)],
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="$avg of two max-coefficient values should produce normalized scientific notation",
    ),
    AvgTest(
        "dec_precision_small_exponent",
        args=DECIMAL128_SMALL_EXPONENT,
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="$avg should preserve small exponent Decimal128 values",
    ),
    AvgTest(
        "dec_precision_small_exponent_with_zero",
        args=[DECIMAL128_SMALL_EXPONENT, DECIMAL128_ZERO],
        expected=Decimal128("5E-6144"),
        msg="$avg of small exponent Decimal128 with zero should halve correctly",
    ),
    AvgTest(
        "dec_precision_small_exponent_cancel",
        args=[DECIMAL128_SMALL_EXPONENT, Decimal128("-1E-6143")],
        expected=Decimal128("0E-6143"),
        msg="$avg should return zero when small exponent Decimal128 values cancel",
    ),
    AvgTest(
        "dec_precision_large_exponent",
        args=DECIMAL128_LARGE_EXPONENT,
        expected=Decimal128("1.000000000000000000000000000000000E+6144"),
        msg="$avg should normalize large exponent to 34-digit coefficient form",
    ),
    AvgTest(
        "dec_precision_large_exponent_with_zero",
        args=[DECIMAL128_LARGE_EXPONENT, DECIMAL128_ZERO],
        expected=Decimal128("5.00000000000000000000000000000000E+6143"),
        msg="$avg of large exponent Decimal128 with zero should halve correctly",
    ),
    AvgTest(
        "dec_precision_large_exponent_cancel",
        args=[DECIMAL128_LARGE_EXPONENT, Decimal128("-1E+6144")],
        expected=DECIMAL128_ZERO,
        msg="$avg should return zero when large exponent Decimal128 values cancel",
    ),
    AvgTest(
        "dec_precision_min_positive",
        args=DECIMAL128_MIN_POSITIVE,
        expected=DECIMAL128_MIN_POSITIVE,
        msg="$avg should preserve min positive Decimal128",
    ),
    AvgTest(
        "dec_precision_min_positive_with_zero",
        args=[DECIMAL128_MIN_POSITIVE, DECIMAL128_ZERO],
        expected=Decimal128("0E-6176"),
        msg="$avg of min positive Decimal128 with zero should preserve exponent",
    ),
    AvgTest(
        "dec_precision_min_positive_cancel",
        args=[DECIMAL128_MAX_NEGATIVE, DECIMAL128_MIN_POSITIVE],
        expected=Decimal128("0E-6176"),
        msg="$avg should return 0E-6176 when min positive Decimal128 values cancel",
    ),
    AvgTest(
        "dec_precision_trailing_zeros_pair",
        args=[Decimal128("1." + "0" * 32), Decimal128("2." + "0" * 32)],
        expected=Decimal128("1.50000000000000000000000000000000"),
        msg="$avg should preserve trailing zeros in a 34-digit pair",
    ),
    AvgTest(
        "dec_precision_min_max_cancel",
        args=[
            Decimal128("-9999999999999999999999999999999999E+6111"),
            Decimal128("9999999999999999999999999999999999E+6111"),
        ],
        expected=DECIMAL128_ZERO,
        msg="$avg of Decimal128 min and max values should produce zero",
    ),
    AvgTest(
        "dec_precision_max_identity",
        args=DECIMAL128_MAX,
        expected=DECIMAL128_MAX,
        msg="$avg of DECIMAL128_MAX should return the correct value",
    ),
    AvgTest(
        "dec_precision_max_with_zero",
        args=[DECIMAL128_MAX, DECIMAL128_ZERO],
        expected=Decimal128("5.000000000000000000000000000000000E+6144"),
        msg="$avg of DECIMAL128_MAX with zero should halve correctly",
    ),
    AvgTest(
        "dec_precision_cross_int32",
        args=[Decimal128("9" * 34), 0],
        expected=Decimal128("5000000000000000000000000000000000"),
        msg="$avg of max-coefficient Decimal128 with int32 zero should halve correctly",
    ),
    AvgTest(
        "dec_precision_cross_double",
        args=[Decimal128("9" * 34), 1.0],
        expected=Decimal128("5.00000000000000000000000000000000E+33"),
        msg="$avg of max-coefficient Decimal128 with double should produce Decimal128 result",
    ),
    # Decimal128 overflow.
    AvgTest(
        "dec_overflow_positive",
        args=[DECIMAL128_MAX, DECIMAL128_MAX],
        expected=DECIMAL128_INFINITY,
        msg="$avg should return Decimal128 Infinity when Decimal128 sum overflows",
    ),
    AvgTest(
        "dec_overflow_negative",
        args=[DECIMAL128_MIN, DECIMAL128_MIN],
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$avg should return Decimal128 -Infinity when negative Decimal128 sum overflows",
    ),
]

# Property [Mixed Double and Decimal128 Precision]: when a double is not
# exactly representable, the full double-to-Decimal128 conversion is visible
# in the result. Exact doubles do not show extra precision.
AVG_MIXED_DOUBLE_DECIMAL_TESTS: list[AvgTest] = [
    AvgTest(
        "mixed_prec_inexact_double",
        args=[3.14, DECIMAL128_ZERO],
        expected=Decimal128("1.570000000000000062172489379008766"),
        msg="$avg should expose full double-to-Decimal128 conversion for inexact double",
    ),
    AvgTest(
        "mixed_prec_0_1_imprecision",
        args=[0.1, Decimal128("0.2")],
        expected=Decimal128("0.1500000000000000027755575615628914"),
        msg="$avg should expose double 0.1 imprecision when mixed with Decimal128",
    ),
    AvgTest(
        "mixed_prec_exact_double",
        args=[4.0, Decimal128("6.0")],
        expected=Decimal128("5.0"),
        msg="$avg should not show extra precision for exact doubles mixed with Decimal128",
    ),
    AvgTest(
        "mixed_prec_no_trailing_zero_from_decimal",
        args=[2.0, Decimal128("4")],
        expected=Decimal128("3"),
        msg="$avg should not add trailing zero when Decimal128 input has none",
    ),
    AvgTest(
        "mixed_prec_int_with_decimal_no_trailing_zero",
        args=[2, Decimal128("4")],
        expected=Decimal128("3"),
        msg="$avg of int and Decimal128 without trailing zero should produce bare integer result",
    ),
    AvgTest(
        "mixed_prec_int_with_decimal_trailing_zero",
        args=[2, Decimal128("4.0")],
        expected=Decimal128("3.0"),
        msg="$avg of int and Decimal128 with trailing zero should preserve it",
    ),
]

AVG_DECIMAL128_ALL_TESTS = AVG_DECIMAL128_PRECISION_TESTS + AVG_MIXED_DOUBLE_DECIMAL_TESTS


@pytest.mark.parametrize("test_case", pytest_params(AVG_DECIMAL128_ALL_TESTS))
def test_avg_decimal128(collection, test_case: AvgTest):
    """Test $avg cases."""
    result = execute_expression(collection, {"$avg": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
