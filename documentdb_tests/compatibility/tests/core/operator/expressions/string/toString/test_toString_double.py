"""$toString double conversion tests: special values, scientific notation, and precision."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Double Conversion]: double values convert to their string representation,
# using scientific notation for magnitudes >= 1e16 or < 1e-4, and preserving special
# values like NaN, Infinity, and negative zero.
TOSTRING_DOUBLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_fractional",
        msg="Fractional double converts to its string representation",
        expression={"$toString": 3.14},
        expected="3.14",
    ),
    ExpressionTestCase(
        "double_negative_fractional",
        msg="Negative fractional double converts correctly",
        expression={"$toString": -3.14},
        expected="-3.14",
    ),
    ExpressionTestCase(
        "double_whole",
        msg="Whole double converts without trailing .0",
        expression={"$toString": 3.0},
        expected="3",
    ),
    ExpressionTestCase(
        "double_negative_whole",
        msg="Negative whole double converts correctly",
        expression={"$toString": -3.0},
        expected="-3",
    ),
    ExpressionTestCase(
        "double_zero",
        msg="Double zero converts to '0'",
        expression={"$toString": DOUBLE_ZERO},
        expected="0",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        msg="Double negative zero converts to '-0'",
        expression={"$toString": DOUBLE_NEGATIVE_ZERO},
        expected="-0",
    ),
    ExpressionTestCase(
        "double_nan",
        msg="Double NaN converts to 'NaN'",
        expression={"$toString": FLOAT_NAN},
        expected="NaN",
    ),
    ExpressionTestCase(
        "double_pos_infinity",
        msg="Infinity converts to 'Infinity'",
        expression={"$toString": FLOAT_INFINITY},
        expected="Infinity",
    ),
    ExpressionTestCase(
        "double_neg_infinity",
        msg="-Infinity converts to '-Infinity'",
        expression={"$toString": FLOAT_NEGATIVE_INFINITY},
        expected="-Infinity",
    ),
    ExpressionTestCase(
        "double_sci_lower_bound",
        msg="1e16 crosses the scientific notation threshold",
        expression={"$toString": 1e16},
        expected="1e+16",
    ),
    ExpressionTestCase(
        "double_sci_lower_bound_neg",
        msg="-1e16 crosses the scientific notation threshold",
        expression={"$toString": -1e16},
        expected="-1e+16",
    ),
    ExpressionTestCase(
        "double_just_below_sci_threshold",
        msg="Value just below 1e16 uses decimal notation",
        expression={"$toString": 9.999999999999998e15},
        expected="9999999999999998",
    ),
    ExpressionTestCase(
        "double_decimal_large",
        msg="1e15 uses decimal notation",
        expression={"$toString": 1e15},
        expected="1000000000000000",
    ),
    ExpressionTestCase(
        "double_sci_small",
        msg="9e-05 is below 1e-4 and uses scientific notation",
        expression={"$toString": 9e-05},
        expected="9e-05",
    ),
    ExpressionTestCase(
        "double_sci_small_neg",
        msg="-9e-05 uses scientific notation",
        expression={"$toString": -9e-05},
        expected="-9e-05",
    ),
    ExpressionTestCase(
        "double_decimal_small_boundary",
        msg="1e-4 is the inclusive lower boundary for decimal notation",
        expression={"$toString": 1e-4},
        expected="0.0001",
    ),
    ExpressionTestCase(
        "double_17_sig_digits",
        msg="17 significant digits of precision are preserved",
        expression={"$toString": 1.0000000000000002},
        expected="1.0000000000000002",
    ),
    ExpressionTestCase(
        "double_subnormal_min",
        msg="Minimum positive subnormal double converts correctly",
        expression={"$toString": DOUBLE_MIN_SUBNORMAL},
        expected="5e-324",
    ),
    ExpressionTestCase(
        "double_subnormal_min_neg",
        msg="Minimum negative subnormal double converts correctly",
        expression={"$toString": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected="-5e-324",
    ),
    ExpressionTestCase(
        "double_subnormal_boundary",
        msg="Subnormal boundary double converts correctly",
        expression={"$toString": 2.2250738585072009e-308},
        expected="2.225073858507201e-308",
    ),
    ExpressionTestCase(
        "double_near_max",
        msg="Near-max double converts correctly",
        expression={"$toString": DOUBLE_MAX},
        expected="1.7976931348623157e+308",
    ),
    ExpressionTestCase(
        "double_near_max_neg",
        msg="Near-max negative double converts correctly",
        expression={"$toString": DOUBLE_MIN},
        expected="-1.7976931348623157e+308",
    ),
    ExpressionTestCase(
        "double_ieee754_artifact",
        msg="IEEE 754 precision artifact from 0.1 + 0.2 is faithfully represented",
        expression={"$toString": {"$add": [0.1, 0.2]}},
        expected="0.30000000000000004",
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOSTRING_DOUBLE_TESTS, "$toString", "string")),
)
def test_toString_double(collection, test: ExpressionTestCase):
    """$toString converts double inputs to their string representation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
