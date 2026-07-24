"""Tests for $log with infinite and NaN value and base inputs."""

import pytest

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
    DECIMAL128_NAN,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [Infinity]: $log of infinity is infinity, $log to an infinite base is zero, and infinity
# in both operands is NaN.
LOG_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity_value",
        doc={"value": FLOAT_INFINITY, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=FLOAT_INFINITY,
        msg="$log should return infinity for an infinite value in base ten",
    ),
    ExpressionTestCase(
        "infinity_value_base2",
        doc={"value": FLOAT_INFINITY, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=FLOAT_INFINITY,
        msg="$log should return infinity for an infinite value in base two",
    ),
    ExpressionTestCase(
        "decimal_infinity_value",
        doc={"value": DECIMAL128_INFINITY, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=DECIMAL128_INFINITY,
        msg="$log should return decimal128 infinity for an infinite decimal128 value",
    ),
    ExpressionTestCase(
        "infinity_base",
        doc={"value": 10, "base": FLOAT_INFINITY},
        expression={"$log": ["$value", "$base"]},
        expected=DOUBLE_ZERO,
        msg="$log should return zero for a finite value in an infinite base",
    ),
    ExpressionTestCase(
        "both_infinity",
        doc={"value": FLOAT_INFINITY, "base": FLOAT_INFINITY},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log should return NaN when both value and base are infinite",
    ),
    ExpressionTestCase(
        "decimal_both_infinity",
        doc={"value": DECIMAL128_INFINITY, "base": DECIMAL128_INFINITY},
        expression={"$log": ["$value", "$base"]},
        expected=DECIMAL128_NAN,
        msg="$log should return decimal128 NaN when both value and base are infinite decimal128",
    ),
]

# Property [NaN]: $log of a NaN value or base returns a double NaN, including for decimal128 NaN
# inputs.
LOG_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_value",
        doc={"value": FLOAT_NAN, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log should return NaN for a NaN value",
    ),
    ExpressionTestCase(
        "nan_base",
        doc={"value": 100, "base": FLOAT_NAN},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log should return NaN for a NaN base",
    ),
    ExpressionTestCase(
        "both_nan",
        doc={"value": FLOAT_NAN, "base": FLOAT_NAN},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log should return NaN when both value and base are NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_value",
        doc={"value": DECIMAL128_NAN, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log should return NaN for a decimal128 NaN value",
    ),
    ExpressionTestCase(
        "decimal_nan_base",
        doc={"value": 100, "base": DECIMAL128_NAN},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log should return NaN for a decimal128 NaN base",
    ),
    ExpressionTestCase(
        "decimal_both_nan",
        doc={"value": DECIMAL128_NAN, "base": DECIMAL128_NAN},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log should return NaN when both value and base are decimal128 NaN",
    ),
]

LOG_NON_FINITE_TESTS = LOG_INFINITY_TESTS + LOG_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LOG_NON_FINITE_TESTS))
def test_log_non_finite(collection, test_case: ExpressionTestCase):
    """Test $log infinity and NaN cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
