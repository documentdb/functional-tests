"""$toInt double conversion tests: truncation, special values, and overflow."""

import pytest

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
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
)

# Property [Double Truncation]: $toInt truncates the fractional part toward zero.
_TOINT_DOUBLE_TRUNCATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_zero",
        msg="0.0 converts to 0",
        expression={"$toInt": DOUBLE_ZERO},
        expected=0,
    ),
    ExpressionTestCase(
        "double_neg_zero",
        msg="-0.0 converts to 0",
        expression={"$toInt": DOUBLE_NEGATIVE_ZERO},
        expected=0,
    ),
    ExpressionTestCase(
        "double_one",
        msg="1.0 converts to 1",
        expression={"$toInt": 1.0},
        expected=1,
    ),
    ExpressionTestCase(
        "double_neg_one",
        msg="-1.0 converts to -1",
        expression={"$toInt": -1.0},
        expected=-1,
    ),
    ExpressionTestCase(
        "double_truncate_positive",
        msg="1.9 is truncated toward zero to 1",
        expression={"$toInt": 1.9},
        expected=1,
    ),
    ExpressionTestCase(
        "double_truncate_negative",
        msg="-1.9 is truncated toward zero to -1",
        expression={"$toInt": -1.9},
        expected=-1,
    ),
    ExpressionTestCase(
        "double_half",
        msg="0.5 is truncated toward zero to 0",
        expression={"$toInt": 0.5},
        expected=0,
    ),
    ExpressionTestCase(
        "double_neg_half",
        msg="-0.5 is truncated toward zero to 0",
        expression={"$toInt": -0.5},
        expected=0,
    ),
]

# Property [Double Boundary]: $toInt accepts doubles in the int32 range;
# rejects NaN, infinity, and out-of-range values.
_TOINT_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_int32_max",
        msg="double equal to int32 max converts exactly",
        expression={"$toInt": float(INT32_MAX)},
        expected=INT32_MAX,
    ),
    ExpressionTestCase(
        "double_int32_min",
        msg="double equal to int32 min converts exactly",
        expression={"$toInt": float(INT32_MIN)},
        expected=INT32_MIN,
    ),
    ExpressionTestCase(
        "double_just_above_max",
        msg="double one above int32 max is a conversion failure",
        expression={"$toInt": float(INT32_MAX) + 1.0},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_just_below_min",
        msg="double one below int32 min is a conversion failure",
        expression={"$toInt": float(INT32_MIN) - 1.0},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_large_positive",
        msg="Large positive double is a conversion failure",
        expression={"$toInt": 1e18},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_large_negative",
        msg="Large negative double is a conversion failure",
        expression={"$toInt": -1e18},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_nan",
        msg="NaN is a conversion failure",
        expression={"$toInt": FLOAT_NAN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_inf",
        msg="+Infinity is a conversion failure",
        expression={"$toInt": FLOAT_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "double_neg_inf",
        msg="-Infinity is a conversion failure",
        expression={"$toInt": FLOAT_NEGATIVE_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOINT_DOUBLE_TESTS = _TOINT_DOUBLE_TRUNCATION_TESTS + _TOINT_DOUBLE_BOUNDARY_TESTS


@pytest.mark.parametrize("test", pytest_params(TOINT_DOUBLE_TESTS))
def test_toInt_double(collection, test: ExpressionTestCase):
    """$toInt truncates doubles toward zero; rejects NaN, infinity, and out-of-range values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
