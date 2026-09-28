"""Tests for $exp of infinity and NaN inputs."""

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
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Infinity]: $exp of positive infinity is infinity and of negative infinity is zero.
EXP_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_infinity",
        doc={"value": FLOAT_INFINITY},
        expression={"$exp": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$exp should return infinity for float infinity",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        expression={"$exp": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$exp should return zero for float negative infinity",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        doc={"value": DECIMAL128_INFINITY},
        expression={"$exp": ["$value"]},
        expected=DECIMAL128_INFINITY,
        msg="$exp should return decimal128 infinity for decimal128 infinity",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$exp": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$exp should return decimal128 zero for decimal128 negative infinity",
    ),
]

# Property [NaN]: $exp of NaN returns NaN of the same type.
EXP_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan",
        doc={"value": FLOAT_NAN},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$exp should return NaN for float NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        doc={"value": DECIMAL128_NAN},
        expression={"$exp": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$exp should return NaN for decimal128 NaN",
    ),
]

EXP_NON_FINITE_TESTS = EXP_INFINITY_TESTS + EXP_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(EXP_NON_FINITE_TESTS))
def test_exp_non_finite(collection, test_case: ExpressionTestCase):
    """Test $exp infinity and NaN cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
