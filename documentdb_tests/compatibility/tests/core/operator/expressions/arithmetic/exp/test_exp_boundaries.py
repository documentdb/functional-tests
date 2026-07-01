"""Tests for $exp at representable-range boundaries, including overflow and underflow."""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MIN,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    INT32_MAX,
    INT64_MAX,
    INT64_MIN,
)

# Property [Overflow]: $exp overflows to infinity past the largest representable exponent and
# underflows to zero for large negative inputs.
EXP_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "just_below_overflow",
        doc={"value": 709},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(8.218407461554972e307),
        msg="$exp should return a large finite double just below the overflow boundary",
    ),
    ExpressionTestCase(
        "overflow",
        doc={"value": 710},
        expression={"$exp": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$exp should return infinity past the overflow boundary",
    ),
    ExpressionTestCase(
        "underflow",
        doc={"value": -750},
        expression={"$exp": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$exp should underflow to zero for a large negative input",
    ),
]

# Property [Integer Boundaries]: $exp of extreme integer inputs overflows to infinity or
# underflows to zero.
EXP_INTEGER_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        doc={"value": INT32_MAX},
        expression={"$exp": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$exp should return infinity for INT32_MAX",
    ),
    ExpressionTestCase(
        "int64_max",
        doc={"value": INT64_MAX},
        expression={"$exp": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$exp should return infinity for INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min",
        doc={"value": INT64_MIN},
        expression={"$exp": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$exp should underflow to zero for INT64_MIN",
    ),
]

# Property [Double Boundaries]: $exp near the double subnormal range returns one, and a large
# double overflows to infinity.
EXP_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_min_subnormal",
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expression={"$exp": ["$value"]},
        expected=1.0,
        msg="$exp should return one for the minimum subnormal double",
    ),
    ExpressionTestCase(
        "double_min_negative_subnormal",
        doc={"value": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expression={"$exp": ["$value"]},
        expected=1.0,
        msg="$exp should return one for the minimum negative subnormal double",
    ),
    ExpressionTestCase(
        "double_near_min",
        doc={"value": DOUBLE_NEAR_MIN},
        expression={"$exp": ["$value"]},
        expected=1.0,
        msg="$exp should return one for a near-zero positive double",
    ),
    ExpressionTestCase(
        "double_precision_loss",
        doc={"value": float(DOUBLE_PRECISION_LOSS)},
        expression={"$exp": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$exp should overflow to infinity for a large double",
    ),
]

# Property [Decimal128 Boundaries]: $exp of extreme decimal128 exponents overflows to infinity or
# underflows to zero, preserving the decimal type.
EXP_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_small_exponent",
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expression={"$exp": ["$value"]},
        expected=Decimal128("1"),
        msg="$exp should return one for a decimal128 with a small exponent",
    ),
    ExpressionTestCase(
        "decimal_large_exponent",
        doc={"value": DECIMAL128_LARGE_EXPONENT},
        expression={"$exp": ["$value"]},
        expected=DECIMAL128_INFINITY,
        msg="$exp should overflow to infinity for a decimal128 with a large exponent",
    ),
    ExpressionTestCase(
        "decimal_max",
        doc={"value": DECIMAL128_MAX},
        expression={"$exp": ["$value"]},
        expected=DECIMAL128_INFINITY,
        msg="$exp should overflow to infinity for decimal128 max",
    ),
    ExpressionTestCase(
        "decimal_min",
        doc={"value": DECIMAL128_MIN},
        expression={"$exp": ["$value"]},
        expected=Decimal128("0E-6176"),
        msg="$exp should underflow to zero for decimal128 min",
    ),
]

EXP_BOUNDARY_ALL_TESTS = (
    EXP_OVERFLOW_TESTS
    + EXP_INTEGER_BOUNDARY_TESTS
    + EXP_DOUBLE_BOUNDARY_TESTS
    + EXP_DECIMAL_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(EXP_BOUNDARY_ALL_TESTS))
def test_exp_boundaries(collection, test_case: ExpressionTestCase):
    """Test $exp representable-range boundary cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
