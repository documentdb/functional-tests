from __future__ import annotations

import math

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.median.utils.median_common import (  # noqa: E501
    MedianTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Core Median Behavior]: $median returns the 50th percentile of
# numeric operands, with negative zero normalized to positive zero.
MEDIAN_CORE_TESTS: list[MedianTest] = [
    MedianTest(
        "core_single_int32",
        args=42,
        expected=42.0,
        msg="$median of a single int32 should return that value as double",
    ),
    MedianTest(
        "core_single_int64",
        args=Int64(42),
        expected=42.0,
        msg="$median of a single int64 should return that value as double",
    ),
    MedianTest(
        "core_single_double",
        args=42.0,
        expected=42.0,
        msg="$median of a single double should return that value",
    ),
    MedianTest(
        "core_single_decimal",
        args=Decimal128("42"),
        expected=Decimal128("42"),
        msg="$median of a single Decimal128 should return that value",
    ),
    MedianTest(
        "core_two_equal",
        args=[5, 5],
        expected=5.0,
        msg="$median of two equal values should return that value",
    ),
    MedianTest(
        "core_multiple_distinct_odd",
        args=[10, 20, 30],
        expected=20.0,
        msg="$median of odd number of elements returns middle element",
    ),
    MedianTest(
        "core_multiple_distinct_even",
        args=[10, 20, 30, 40],
        expected=25.0,
        msg="$median of even number of elements returns average of middle elements",
    ),
    MedianTest(
        "core_positive_negative_cancel",
        args=[1, -1],
        expected=DOUBLE_ZERO,
        msg="$median of positive and negative values that cancel should return 0.0",
    ),
    MedianTest(
        "core_negative_values_odd",
        args=[-10, -20, -30],
        expected=-20.0,
        msg="$median of negative values returns correct negative median",
    ),
    MedianTest(
        "core_negative_values_even",
        args=[-10, -20],
        expected=-15.0,
        msg="$median of negative values returns correct negative median",
    ),
    MedianTest(
        "core_zero",
        args=0,
        expected=DOUBLE_ZERO,
        msg="$median of zero should return 0.0",
    ),
    MedianTest(
        "core_zero_pair",
        args=[0, 0],
        expected=DOUBLE_ZERO,
        msg="$median of two zeros should return 0.0",
    ),
    MedianTest(
        "core_neg_zero_double",
        args=DOUBLE_NEGATIVE_ZERO,
        expected=DOUBLE_ZERO,
        msg="$median should normalize double negative zero to positive zero",
    ),
    MedianTest(
        "core_neg_zero_double_in_list",
        args=[DOUBLE_NEGATIVE_ZERO, DOUBLE_NEGATIVE_ZERO],
        expected=DOUBLE_ZERO,
        msg="$median should normalize double negative zero to positive zero in a list",
    ),
    MedianTest(
        "core_neg_zero_pos_zero_cancel",
        args=[DOUBLE_NEGATIVE_ZERO, DOUBLE_ZERO],
        expected=DOUBLE_ZERO,
        msg="$median of -0.0 and 0.0 should return positive zero",
    ),
    MedianTest(
        "core_neg_zero_decimal",
        args=DECIMAL128_NEGATIVE_ZERO,
        expected=DECIMAL128_ZERO,
        msg="$median should normalize Decimal128 negative zero to positive zero",
    ),
    MedianTest(
        "core_neg_zero_decimal_in_list",
        args=[DECIMAL128_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        expected=DECIMAL128_ZERO,
        msg="$median should normalize Decimal128 negative zero to positive zero in a list",
    ),
    MedianTest(
        "core_neg_zero_pos_zero_decimal_cancel",
        args=[DECIMAL128_NEGATIVE_ZERO, DECIMAL128_ZERO],
        expected=DECIMAL128_ZERO,
        msg="$median of Decimal128 -0 and 0 should return positive Decimal128 zero",
    ),
]

# Property [NaN and Infinity]: NaN propagates through median and dominates
# Infinity. Infinity propagates when mixed with finite values. Cancellation
# of Infinity and -Infinity produces NaN. Decimal128 variants follow the
# same rules but produce Decimal128 results.
MEDIAN_NAN_INFINITY_TESTS: list[MedianTest] = [
    MedianTest(
        "nan_scalar",
        args=FLOAT_NAN,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$median should return NaN for a NaN scalar operand",
    ),
    MedianTest(
        "nan_pair",
        args=[FLOAT_NAN, FLOAT_NAN],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$median of two NaN values should return NaN",
    ),
    MedianTest(
        "inf_scalar",
        args=FLOAT_INFINITY,
        expected=FLOAT_INFINITY,
        msg="$median should return Infinity for an Infinity scalar operand",
    ),
    MedianTest(
        "inf_pair",
        args=[FLOAT_INFINITY, FLOAT_INFINITY],
        expected=FLOAT_INFINITY,
        msg="$median of two Infinity values should return Infinity",
    ),
    MedianTest(
        "neg_inf_scalar",
        args=FLOAT_NEGATIVE_INFINITY,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$median should return -Infinity for a -Infinity scalar operand",
    ),
    MedianTest(
        "neg_inf_pair",
        args=[FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$median of two -Infinity values should return -Infinity",
    ),
    MedianTest(
        "decimal_nan_scalar",
        args=DECIMAL128_NAN,
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN for a Decimal128 NaN scalar operand",
    ),
    MedianTest(
        "decimal_nan_pair",
        args=[DECIMAL128_NAN, DECIMAL128_NAN],
        expected=DECIMAL128_NAN,
        msg="$median of two Decimal128 NaN values should return Decimal128 NaN",
    ),
    MedianTest(
        "decimal_inf_scalar",
        args=DECIMAL128_INFINITY,
        expected=DECIMAL128_INFINITY,
        msg="$median should return Decimal128 Infinity for a Decimal128 Infinity scalar operand",
    ),
    MedianTest(
        "decimal_inf_pair",
        args=[DECIMAL128_INFINITY, DECIMAL128_INFINITY],
        expected=DECIMAL128_INFINITY,
        msg="$median of two Decimal128 Infinity values should return Decimal128 Infinity",
    ),
    MedianTest(
        "decimal_neg_inf_scalar",
        args=DECIMAL128_NEGATIVE_INFINITY,
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$median should return Decimal128 -Infinity for a Decimal128 -Infinity scalar operand",
    ),
    MedianTest(
        "decimal_neg_inf_pair",
        args=[DECIMAL128_NEGATIVE_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$median of two Decimal128 -Infinity values should return Decimal128 -Infinity",
    ),
    MedianTest(
        "nan_with_numeric",
        args=[FLOAT_NAN, 5],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$median should return NaN when NaN is mixed with a numeric value",
    ),
    MedianTest(
        "nan_with_null",
        args=[FLOAT_NAN, None],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$median should return NaN when NaN is mixed with null",
    ),
    MedianTest(
        "nan_dominates_inf",
        args=[FLOAT_NAN, FLOAT_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$median should return NaN when NaN is mixed with Infinity",
    ),
    MedianTest(
        "inf_with_finite",
        args=[FLOAT_INFINITY, 5],
        expected=FLOAT_INFINITY,
        msg="$median should return Infinity when Infinity is mixed with finite value",
    ),
    MedianTest(
        "neg_inf_with_finite",
        args=[FLOAT_NEGATIVE_INFINITY, 5],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$median should return -Infinity when -Infinity is mixed with finite value",
    ),
    MedianTest(
        "inf_neg_inf_cancel",
        args=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$median should return NaN when Infinity and -Infinity cancel",
    ),
    MedianTest(
        "inf_with_null",
        args=[FLOAT_INFINITY, None],
        expected=FLOAT_INFINITY,
        msg="$median should return Infinity when Infinity is mixed with null",
    ),
    MedianTest(
        "decimal_nan_with_numeric",
        args=[DECIMAL128_NAN, Decimal128("5")],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN when Decimal128 NaN is present",
    ),
    MedianTest(
        "decimal_inf_with_finite",
        args=[DECIMAL128_INFINITY, Decimal128("5")],
        expected=DECIMAL128_INFINITY,
        msg="$median should return Decimal128 Infinity with finite Decimal128",
    ),
    MedianTest(
        "decimal_neg_inf_with_finite",
        args=[DECIMAL128_NEGATIVE_INFINITY, Decimal128("5")],
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$median should return Decimal128 -Infinity with finite Decimal128",
    ),
    MedianTest(
        "decimal_inf_neg_inf_cancel",
        args=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN when Decimal128 Inf and -Inf cancel",
    ),
    MedianTest(
        "decimal_negative_nan_preserved",
        args=DECIMAL128_NEGATIVE_NAN,
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$median should preserve Decimal128 -NaN sign bit",
    ),
    MedianTest(
        "decimal_nan_dominates_inf",
        args=[DECIMAL128_NAN, DECIMAL128_INFINITY],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN when NaN dominates Decimal128 Infinity",
    ),
    MedianTest(
        "decimal_nan_with_null",
        args=[DECIMAL128_NAN, None],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN when mixed with null",
    ),
    MedianTest(
        "decimal_inf_with_null",
        args=[DECIMAL128_INFINITY, None],
        expected=DECIMAL128_INFINITY,
        msg="$median should return Decimal128 Infinity when mixed with null",
    ),
    # Cross-type: double NaN + Decimal128 value produces Decimal128 NaN.
    MedianTest(
        "cross_double_nan_decimal_value",
        args=[FLOAT_NAN, Decimal128("5")],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN for double NaN + Decimal128 value",
    ),
    MedianTest(
        "cross_decimal_nan_int32",
        args=[DECIMAL128_NAN, 5],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN for Decimal128 NaN + int32",
    ),
    # Cross-type Infinity cancellation produces Decimal128 NaN.
    MedianTest(
        "cross_decimal_inf_double_neg_inf",
        args=[DECIMAL128_INFINITY, FLOAT_NEGATIVE_INFINITY],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN for Decimal128 Inf + double -Inf",
    ),
    MedianTest(
        "cross_double_inf_decimal_neg_inf",
        args=[FLOAT_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        expected=DECIMAL128_NAN,
        msg="$median should return Decimal128 NaN for double Inf + Decimal128 -Inf",
    ),
]

MEDIAN_CORE_ALL_TESTS = MEDIAN_CORE_TESTS + MEDIAN_NAN_INFINITY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MEDIAN_CORE_ALL_TESTS))
def test_median_core(collection, test_case: MedianTest):
    """Test $median cases."""
    result = execute_expression(
        collection, {"$median": {"input": test_case.args, "method": "approximate"}}
    )
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
