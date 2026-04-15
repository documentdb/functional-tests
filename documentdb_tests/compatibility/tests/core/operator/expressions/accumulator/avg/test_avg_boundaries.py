from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.avg.utils.avg_common import (  # noqa: E501
    AvgTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_INT64_UNDERFLOW,
    DECIMAL128_NEGATIVE_HALF,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_NORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
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

# Property [Integer Boundary Behavior]: int32 and int64 boundary values
# produce correct double results, with int64 boundaries exhibiting
# precision loss. Decimal128 preserves full precision at these boundaries.
AVG_INTEGER_BOUNDARY_TESTS: list[AvgTest] = [
    # Individual int32 boundary values as single-value averages.
    AvgTest(
        "intbound_int32_max",
        args=INT32_MAX,
        expected=float(INT32_MAX),
        msg="$avg of the int32 upper boundary should return the correct double",
    ),
    AvgTest(
        "intbound_int32_max_minus_1",
        args=INT32_MAX_MINUS_1,
        expected=float(INT32_MAX_MINUS_1),
        msg="$avg of one below the int32 upper boundary should return the correct double",
    ),
    AvgTest(
        "intbound_int32_min",
        args=INT32_MIN,
        expected=float(INT32_MIN),
        msg="$avg of the int32 lower boundary should return the correct double",
    ),
    AvgTest(
        "intbound_int32_min_plus_1",
        args=INT32_MIN_PLUS_1,
        expected=float(INT32_MIN_PLUS_1),
        msg="$avg of one above the int32 lower boundary should return the correct double",
    ),
    AvgTest(
        "intbound_int32_max_pair",
        args=[INT32_MAX, INT32_MAX],
        expected=float(INT32_MAX),
        msg="$avg of two INT32_MAX values should return INT32_MAX as double",
    ),
    AvgTest(
        "intbound_int32_max_adjacent",
        args=[INT32_MAX, INT32_MAX_MINUS_1],
        expected=2_147_483_646.5,
        msg="$avg of INT32_MAX and INT32_MAX_MINUS_1 should return the correct midpoint",
    ),
    # Individual int64 boundary values lose precision when converted to double.
    AvgTest(
        "intbound_int64_max",
        args=INT64_MAX,
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$avg of the int64 upper boundary should return double with precision loss",
    ),
    AvgTest(
        "intbound_int64_max_minus_1",
        args=INT64_MAX_MINUS_1,
        expected=DOUBLE_FROM_INT64_MAX,
        msg=(
            "$avg of one below the int64 upper boundary"
            " should map to the same double as the upper boundary"
        ),
    ),
    AvgTest(
        "intbound_int64_min",
        args=INT64_MIN,
        expected=-DOUBLE_FROM_INT64_MAX,
        msg="$avg of the int64 lower boundary should return double with precision loss",
    ),
    AvgTest(
        "intbound_int64_min_plus_1",
        args=INT64_MIN_PLUS_1,
        expected=-DOUBLE_FROM_INT64_MAX,
        msg="$avg of one above the int64 lower boundary should map to the same double",
    ),
    AvgTest(
        "intbound_int64_max_identical",
        args=[INT64_MAX, INT64_MAX],
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$avg of two INT64_MAX values should return INT64_MAX as double",
    ),
    AvgTest(
        "intbound_int64_min_adjacent",
        args=[INT64_MIN, INT64_MIN_PLUS_1],
        expected=-DOUBLE_FROM_INT64_MAX,
        msg="$avg of INT64_MIN and INT64_MIN_PLUS_1 should return double with precision loss",
    ),
    # Averaging the int32 upper and lower boundaries yields -0.5 (they differ by 1).
    AvgTest(
        "intbound_int32_max_min_avg",
        args=[INT32_MAX, INT32_MIN],
        expected=-0.5,
        msg="$avg of int32 upper and lower boundaries should return -0.5",
    ),
    # Averaging the int64 upper and lower boundaries yields 0.0 due to double precision loss.
    AvgTest(
        "intbound_int64_max_min_cancel",
        args=[INT64_MAX, INT64_MIN],
        expected=DOUBLE_ZERO,
        msg=(
            "$avg of the int64 upper and lower boundaries should"
            " return 0.0 due to double precision loss"
        ),
    ),
    # Decimal128 preserves precision for the same pair.
    AvgTest(
        "intbound_decimal_int64_max_min",
        args=[Decimal128("9223372036854775807"), Decimal128("-9223372036854775808")],
        expected=DECIMAL128_NEGATIVE_HALF,
        msg="$avg of Decimal128 int64 upper and lower boundaries should preserve precision",
    ),
    # The int64 upper boundary and one below it produce the same double due to precision loss.
    AvgTest(
        "intbound_int64_max_pair",
        args=[INT64_MAX, INT64_MAX_MINUS_1],
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$avg of the int64 upper boundary and one below it should return the same double",
    ),
    # Boundary pairs across int32/int64 boundaries.
    AvgTest(
        "intbound_int32_max_int64_next",
        args=[INT32_MAX, Int64(INT32_MAX + 1)],
        expected=2_147_483_647.5,
        msg="$avg across the int32/int64 boundary should return the correct midpoint",
    ),
    AvgTest(
        "intbound_int32_min_int64_prev",
        args=[INT32_MIN, Int64(INT32_MIN - 1)],
        expected=-2_147_483_648.5,
        msg="$avg across the int32/int64 lower boundary should return the correct midpoint",
    ),
    # Decimal128 preserves precision for values beyond int64 range.
    AvgTest(
        "intbound_decimal_beyond_int64",
        args=[DECIMAL128_INT64_OVERFLOW, DECIMAL128_INT64_UNDERFLOW],
        expected=DECIMAL128_NEGATIVE_HALF,
        msg="$avg of Decimal128 values beyond int64 range should preserve precision",
    ),
    # int64 overflow: values are converted to double before summing.
    AvgTest(
        "intbound_int64_overflow_follows_double",
        args=[INT64_MAX, INT64_MAX],
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$avg should convert int64 to double before summing, avoiding integer overflow",
    ),
    AvgTest(
        "intbound_int64_negative_overflow_follows_double",
        args=[INT64_MIN, INT64_MIN],
        expected=-DOUBLE_FROM_INT64_MAX,
        msg="$avg should convert negative int64 to double before summing, avoiding underflow",
    ),
]

# Property [Float Boundary Behavior]: float boundary values including
# subnormals, near-max-finite doubles, and IEEE 754 imprecision are
# handled correctly by $avg.
AVG_FLOAT_BOUNDARY_TESTS: list[AvgTest] = [
    # Individual float boundary values as single-value averages.
    AvgTest(
        "floatbound_1e20",
        args=1e20,
        expected=1e20,
        msg="$avg of 1e20 should return the correct double",
    ),
    AvgTest(
        "floatbound_neg_min_subnormal",
        args=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        expected=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        msg="$avg of min negative subnormal should return the correct double",
    ),
    AvgTest(
        "floatbound_dbl_min",
        args=DOUBLE_MIN_NORMAL,
        expected=DOUBLE_MIN_NORMAL,
        msg="$avg of DBL_MIN should return the correct double",
    ),
    AvgTest(
        "floatbound_1e_neg308",
        args=DOUBLE_NEAR_MIN,
        expected=DOUBLE_NEAR_MIN,
        msg="$avg of a small double near the normal minimum should return correctly",
    ),
    AvgTest(
        "floatbound_1e308",
        args=DOUBLE_NEAR_MAX,
        expected=DOUBLE_NEAR_MAX,
        msg="$avg of a large double near the finite maximum should return correctly",
    ),
    AvgTest(
        "floatbound_int64_max_as_double",
        args=DOUBLE_FROM_INT64_MAX,
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$avg of the int64 upper boundary as double should return the correct double",
    ),
    AvgTest(
        "floatbound_max_safe_int",
        args=DOUBLE_MAX_SAFE_INTEGER,
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$avg of max safe integer should return the correct double",
    ),
    # The precision-loss integer rounds to the same double as max safe integer.
    AvgTest(
        "floatbound_precision_loss_int",
        args=DOUBLE_PRECISION_LOSS,
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$avg of precision-loss integer should round to max safe integer double",
    ),
    AvgTest(
        "floatbound_fractional",
        args=0.123456789,
        expected=0.123456789,
        msg="$avg of a fractional double should return the correct value",
    ),
    AvgTest(
        "floatbound_whole_number_float",
        args=3.0,
        expected=3.0,
        msg="$avg of a whole-number float should return the correct double",
    ),
    # Subnormal preservation and underflow.
    AvgTest(
        "floatbound_subnormal_preserved",
        args=[DOUBLE_MIN_SUBNORMAL, DOUBLE_MIN_SUBNORMAL],
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="$avg should preserve subnormal when the result is exact",
    ),
    AvgTest(
        "floatbound_subnormal_underflow",
        args=[DOUBLE_MIN_SUBNORMAL, DOUBLE_ZERO],
        expected=DOUBLE_ZERO,
        msg="$avg should underflow to zero when subnormal is divided by 2",
    ),
    AvgTest(
        "floatbound_subnormal_cancel",
        args=[DOUBLE_MIN_NEGATIVE_SUBNORMAL, DOUBLE_MIN_SUBNORMAL],
        expected=DOUBLE_ZERO,
        msg="$avg should return 0.0 when subnormals cancel",
    ),
    # Near-max-finite doubles.
    AvgTest(
        "floatbound_dbl_max_identity",
        args=DOUBLE_MAX,
        expected=DOUBLE_MAX,
        msg="$avg of DBL_MAX should return the correct double",
    ),
    AvgTest(
        "floatbound_dbl_max_cancel",
        args=[DOUBLE_MAX, -DOUBLE_MAX],
        expected=DOUBLE_ZERO,
        msg="$avg should return 0.0 when DBL_MAX and -DBL_MAX cancel",
    ),
    AvgTest(
        "floatbound_dbl_max_with_zero",
        args=[DOUBLE_MAX, 0],
        expected=8.988465674311579e307,
        msg="$avg of DBL_MAX with zero should return half of DBL_MAX without overflow",
    ),
    AvgTest(
        "floatbound_near_max_cancel",
        args=[DOUBLE_NEAR_MAX, -DOUBLE_NEAR_MAX],
        expected=DOUBLE_ZERO,
        msg="$avg should return 0.0 when near-max-finite doubles cancel",
    ),
    AvgTest(
        "floatbound_large_with_zero",
        args=[1e20, 0],
        expected=5e19,
        msg="$avg of a large value with zero should return half the large value",
    ),
    AvgTest(
        "floatbound_dbl_min_with_zero",
        args=[DOUBLE_MIN_NORMAL, 0],
        expected=1.1125369292536007e-308,
        msg="$avg of DBL_MIN with zero should return half of DBL_MIN",
    ),
    AvgTest(
        "floatbound_dbl_min_cancel",
        args=[DOUBLE_MIN_NORMAL, -DOUBLE_MIN_NORMAL],
        expected=DOUBLE_ZERO,
        msg="$avg should return 0.0 when DBL_MIN and -DBL_MIN cancel",
    ),
    # IEEE 754 imprecision is observable.
    AvgTest(
        "floatbound_ieee_imprecision",
        args=[0.1, 0.2],
        expected=0.15000000000000002,
        msg="$avg should exhibit IEEE 754 imprecision for 0.1 and 0.2",
    ),
    AvgTest(
        "floatbound_accumulated_imprecision",
        args=[0.1, 0.1, 0.1],
        expected=0.10000000000000002,
        msg="$avg should exhibit accumulated imprecision with repeated 0.1",
    ),
    # Double overflow.
    AvgTest(
        "floatbound_overflow_positive",
        args=[DOUBLE_MAX, DOUBLE_MAX],
        expected=FLOAT_INFINITY,
        msg="$avg should return Infinity when double sum overflows",
    ),
    AvgTest(
        "floatbound_overflow_negative",
        args=[-DOUBLE_MAX, -DOUBLE_MAX],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$avg should return -Infinity when negative double sum overflows",
    ),
]

AVG_BOUNDARY_ALL_TESTS = AVG_INTEGER_BOUNDARY_TESTS + AVG_FLOAT_BOUNDARY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(AVG_BOUNDARY_ALL_TESTS))
def test_avg_boundary(collection, test_case: AvgTest):
    """Test $avg cases."""
    result = execute_expression(collection, {"$avg": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
