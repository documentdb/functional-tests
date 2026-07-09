"""
Value error tests for $range expression.

Tests non-integral values, special numeric values (NaN, Infinity),
step zero, out-of-int32-range values, and wrong arity.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    RANGE_END_NOT_INT32_ERROR,
    RANGE_START_NOT_INTEGRAL_ERROR,
    RANGE_STEP_NOT_INT32_ERROR,
    RANGE_STEP_ZERO_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Non-Integral Start]: $range rejects fractional numeric values for start.
NON_INTEGRAL_START_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "fractional_start",
        doc={"start": 1.5, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject fractional start",
    ),
    ExpressionTestCase(
        "decimal128_fractional_start",
        doc={"start": DECIMAL128_HALF, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject fractional Decimal128 start",
    ),
    ExpressionTestCase(
        "negative_fractional_start",
        doc={"start": -1.5, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject negative fractional start",
    ),
    ExpressionTestCase(
        "decimal128_negative_fractional_start",
        doc={"start": DECIMAL128_NEGATIVE_ONE_AND_HALF, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject negative fractional Decimal128 start",
    ),
    ExpressionTestCase(
        "decimal128_negative_nan_start",
        doc={"start": DECIMAL128_NEGATIVE_NAN, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject Decimal128 -NaN start",
    ),
]

# Property [Non-Integral End]: $range rejects fractional numeric values for end.
NON_INTEGRAL_END_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "fractional_end",
        doc={"start": 0, "end": 5.5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject fractional end",
    ),
    ExpressionTestCase(
        "decimal128_fractional_end",
        doc={"start": 0, "end": Decimal128("5.5")},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject fractional Decimal128 end",
    ),
    ExpressionTestCase(
        "negative_fractional_end",
        doc={"start": 0, "end": -1.5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject negative fractional end",
    ),
    ExpressionTestCase(
        "decimal128_negative_fractional_end",
        doc={"start": 0, "end": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject negative fractional Decimal128 end",
    ),
]

# Property [Non-Integral Step]: $range rejects fractional numeric values for step.
NON_INTEGRAL_STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "fractional_step",
        doc={"start": 0, "end": 10, "step": 1.5},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="$range should reject fractional step",
    ),
    ExpressionTestCase(
        "decimal128_fractional_step",
        doc={"start": 0, "end": 10, "step": DECIMAL128_ONE_AND_HALF},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="$range should reject fractional Decimal128 step",
    ),
    ExpressionTestCase(
        "negative_fractional_step",
        doc={"start": 10, "end": 0, "step": -1.5},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="$range should reject negative fractional step",
    ),
    ExpressionTestCase(
        "decimal128_negative_fractional_step",
        doc={"start": 10, "end": 0, "step": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="$range should reject negative fractional Decimal128 step",
    ),
]

# Property [Special Numeric Values]: $range rejects NaN and Infinity values.
# Property [Special Numerics]: $range rejects NaN and Infinity values.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_start",
        doc={"start": FLOAT_NAN, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject NaN start",
    ),
    ExpressionTestCase(
        "inf_start",
        doc={"start": FLOAT_INFINITY, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject Infinity start",
    ),
    ExpressionTestCase(
        "neg_inf_start",
        doc={"start": FLOAT_NEGATIVE_INFINITY, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject -Infinity start",
    ),
    ExpressionTestCase(
        "nan_end",
        doc={"start": 0, "end": FLOAT_NAN},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject NaN end",
    ),
    ExpressionTestCase(
        "inf_end",
        doc={"start": 0, "end": FLOAT_INFINITY},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject Infinity end",
    ),
    ExpressionTestCase(
        "decimal128_nan_start",
        doc={"start": DECIMAL128_NAN, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject Decimal128 NaN start",
    ),
    ExpressionTestCase(
        "decimal128_inf_start",
        doc={"start": DECIMAL128_INFINITY, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject Decimal128 Infinity start",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf_end",
        doc={"start": 0, "end": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject Decimal128 -Infinity end",
    ),
]

# Property [Step Zero]: $range rejects zero step value.
STEP_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "step_zero_int",
        doc={"start": 0, "end": 5, "step": 0},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="$range should reject step 0",
    ),
    ExpressionTestCase(
        "step_zero_int64",
        doc={"start": 0, "end": 5, "step": INT64_ZERO},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="$range should reject Int64 step 0",
    ),
    ExpressionTestCase(
        "step_zero_double",
        doc={"start": 0, "end": 5, "step": DOUBLE_ZERO},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="$range should reject double step 0.0",
    ),
    ExpressionTestCase(
        "step_zero_decimal128",
        doc={"start": 0, "end": 5, "step": DECIMAL128_ZERO},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="$range should reject Decimal128 step 0",
    ),
    ExpressionTestCase(
        "step_neg_zero_double",
        doc={"start": 0, "end": 5, "step": DOUBLE_NEGATIVE_ZERO},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="$range should reject negative zero double step",
    ),
    ExpressionTestCase(
        "step_neg_zero_decimal128",
        doc={"start": 0, "end": 5, "step": DECIMAL128_NEGATIVE_ZERO},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="$range should reject negative zero Decimal128 step",
    ),
]

# Property [Out of INT32 Range]: $range rejects values outside int32 range.
OUT_OF_INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "start_int64_max",
        doc={"start": INT64_MAX, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject INT64_MAX start",
    ),
    ExpressionTestCase(
        "start_int64_min",
        doc={"start": INT64_MIN, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject INT64_MIN start",
    ),
    ExpressionTestCase(
        "end_int64_max",
        doc={"start": 0, "end": INT64_MAX},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject INT64_MAX end",
    ),
    ExpressionTestCase(
        "end_int64_min",
        doc={"start": 0, "end": INT64_MIN},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject INT64_MIN end",
    ),
    ExpressionTestCase(
        "step_int64_max",
        doc={"start": 0, "end": 5, "step": INT64_MAX},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="$range should reject INT64_MAX step",
    ),
    ExpressionTestCase(
        "start_int32_overflow",
        doc={"start": INT32_OVERFLOW, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject INT32_OVERFLOW start",
    ),
    ExpressionTestCase(
        "start_int32_underflow",
        doc={"start": INT32_UNDERFLOW, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="$range should reject INT32_UNDERFLOW start",
    ),
    ExpressionTestCase(
        "end_int32_overflow",
        doc={"start": 0, "end": INT32_OVERFLOW},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject INT32_OVERFLOW end",
    ),
    ExpressionTestCase(
        "end_int32_underflow",
        doc={"start": 0, "end": INT32_UNDERFLOW},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="$range should reject INT32_UNDERFLOW end",
    ),
    ExpressionTestCase(
        "step_int32_overflow",
        doc={"start": 0, "end": 5, "step": INT32_OVERFLOW},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="$range should reject INT32_OVERFLOW step",
    ),
    ExpressionTestCase(
        "step_int32_underflow",
        doc={"start": 0, "end": 5, "step": INT32_UNDERFLOW},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="$range should reject INT32_UNDERFLOW step",
    ),
]

# Property [Arity]: $range rejects wrong number of arguments.
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$range": []},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$range should error with zero arguments",
    ),
    ExpressionTestCase(
        "one_arg",
        expression={"$range": [1]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$range should error with one argument",
    ),
    ExpressionTestCase(
        "four_args",
        expression={"$range": [1, 2, 3, 4]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$range should error with four arguments",
    ),
]

ALL_TESTS = (
    NON_INTEGRAL_START_TESTS
    + NON_INTEGRAL_END_TESTS
    + NON_INTEGRAL_STEP_TESTS
    + SPECIAL_NUMERIC_TESTS
    + STEP_ZERO_TESTS
    + OUT_OF_INT32_TESTS
    + ARITY_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_range_value_error(collection, test):
    """Test $range error with invalid numeric values."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
