"""$toLong numeric type tests: null/missing, boolean, int32, int64 identity, and double."""

import math

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_HALF,
    DOUBLE_MAX_FITTING_INT64,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_FROM_DOUBLE_MAX_FITTING,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
    INT64_ZERO,
    MISSING,
)

# Property [Null and Missing]: $toLong returns null for null and missing inputs.
TOLONG_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null", msg="Should return null for null", expression={"$toLong": None}, expected=None
    ),
    ExpressionTestCase(
        "missing",
        msg="Should return null for missing",
        expression={"$toLong": MISSING},
        expected=None,
    ),
]

# Property [Boolean]: $toLong converts false to Int64(0) and true to Int64(1).
TOLONG_BOOL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_false",
        msg="False converts to Int64(0)",
        expression={"$toLong": False},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "bool_true",
        msg="True converts to Int64(1)",
        expression={"$toLong": True},
        expected=Int64(1),
    ),
]

# Property [Int32]: $toLong widens int32 values to their exact Int64 equivalents.
TOLONG_INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        msg="int32 zero widens to Int64(0)",
        expression={"$toLong": INT32_ZERO},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "int32_one",
        msg="int32 1 widens to Int64(1)",
        expression={"$toLong": 1},
        expected=Int64(1),
    ),
    ExpressionTestCase(
        "int32_neg_one",
        msg="int32 -1 widens to Int64(-1)",
        expression={"$toLong": -1},
        expected=Int64(-1),
    ),
    ExpressionTestCase(
        "int32_max",
        msg="int32 max widens exactly to Int64",
        expression={"$toLong": INT32_MAX},
        expected=Int64(INT32_MAX),
    ),
    ExpressionTestCase(
        "int32_min",
        msg="int32 min widens exactly to Int64",
        expression={"$toLong": INT32_MIN},
        expected=Int64(INT32_MIN),
    ),
]

# Property [Int64 Identity]: $toLong passes Int64 values through unchanged.
TOLONG_INT64_IDENTITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_zero",
        msg="Int64(0) passes through unchanged",
        expression={"$toLong": INT64_ZERO},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "int64_max",
        msg="Int64 max passes through unchanged",
        expression={"$toLong": INT64_MAX},
        expected=INT64_MAX,
    ),
    ExpressionTestCase(
        "int64_min",
        msg="Int64 min passes through unchanged",
        expression={"$toLong": INT64_MIN},
        expected=INT64_MIN,
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        msg="Int64 max minus 1 passes through unchanged",
        expression={"$toLong": INT64_MAX_MINUS_1},
        expected=INT64_MAX_MINUS_1,
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        msg="Int64 min plus 1 passes through unchanged",
        expression={"$toLong": INT64_MIN_PLUS_1},
        expected=INT64_MIN_PLUS_1,
    ),
]

# Property [Double Conversion]: $toLong truncates doubles toward zero; whole-number doubles
# convert exactly, and boundary values at the edges of int64 range are accepted.
TOLONG_DOUBLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_whole",
        msg="Whole-number double converts to Int64",
        expression={"$toLong": 3.0},
        expected=Int64(3),
    ),
    ExpressionTestCase(
        "double_negative_whole",
        msg="Negative whole-number double converts to Int64",
        expression={"$toLong": -5.0},
        expected=Int64(-5),
    ),
    ExpressionTestCase(
        "double_truncate_positive",
        msg="Positive fractional double is truncated toward zero",
        expression={"$toLong": 1.99999},
        expected=Int64(1),
    ),
    ExpressionTestCase(
        "double_truncate_negative",
        msg="Negative fractional double is truncated toward zero",
        expression={"$toLong": -3.14},
        expected=Int64(-3),
    ),
    ExpressionTestCase(
        "double_negative_zero",
        msg="-0.0 converts to Int64(0)",
        expression={"$toLong": DOUBLE_NEGATIVE_ZERO},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "double_half_positive",
        msg="0.5 is truncated toward zero to Int64(0)",
        expression={"$toLong": DOUBLE_HALF},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "double_half_negative",
        msg="-0.5 is truncated toward zero to Int64(0)",
        expression={"$toLong": DOUBLE_NEGATIVE_HALF},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "double_subnormal",
        msg="Subnormal double is truncated to Int64(0)",
        expression={"$toLong": DOUBLE_MIN_SUBNORMAL},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "double_small_positive",
        msg="Small positive double near min is truncated to Int64(0)",
        expression={"$toLong": DOUBLE_NEAR_MIN},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "double_max_fitting",
        msg="Largest double fitting in int64 range converts to its truncated Int64 value",
        expression={"$toLong": DOUBLE_MAX_FITTING_INT64},
        expected=INT64_FROM_DOUBLE_MAX_FITTING,
    ),
    ExpressionTestCase(
        "double_int64_min_exact",
        msg="int64 min as an exact double converts to Int64 min",
        expression={"$toLong": -DOUBLE_FROM_INT64_MAX},
        expected=INT64_MIN,
    ),
]

# Property [Double Conversion Errors]: NaN, infinities, and doubles outside int64 range
# produce a conversion error.
TOLONG_DOUBLE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_err_nan",
        msg="NaN is a conversion failure",
        expression={"$toLong": FLOAT_NAN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_err_pos_infinity",
        msg="+Infinity is a conversion failure",
        expression={"$toLong": FLOAT_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_err_neg_infinity",
        msg="-Infinity is a conversion failure",
        expression={"$toLong": FLOAT_NEGATIVE_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_err_overflow_2_63",
        msg="Double at 2**63 (first above int64 max) is a conversion failure",
        expression={"$toLong": float(2**63)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_err_overflow_large",
        msg="Very large double is a conversion failure",
        expression={"$toLong": DOUBLE_NEAR_MAX},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_err_underflow_below_int64_min",
        msg="First double below int64 min is a conversion failure",
        expression={"$toLong": math.nextafter(-float(2**63), FLOAT_NEGATIVE_INFINITY)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_err_underflow_large_negative",
        msg="Very large negative double is a conversion failure",
        expression={"$toLong": -DOUBLE_NEAR_MAX},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOLONG_NUMERIC_TESTS = (
    TOLONG_NULL_MISSING_TESTS
    + TOLONG_BOOL_TESTS
    + TOLONG_INT32_TESTS
    + TOLONG_INT64_IDENTITY_TESTS
    + TOLONG_DOUBLE_TESTS
    + TOLONG_DOUBLE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TOLONG_NUMERIC_TESTS))
def test_toLong_numeric(collection, test: ExpressionTestCase):
    """$toLong converts null, bool, int32, int64, and double inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
