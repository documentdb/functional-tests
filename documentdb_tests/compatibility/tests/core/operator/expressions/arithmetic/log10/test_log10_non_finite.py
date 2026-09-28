"""Tests for $log10 of positive infinity and NaN inputs."""

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
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [Infinity]: $log10 of positive infinity is infinity of the same type.
LOG10_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_infinity",
        doc={"value": FLOAT_INFINITY},
        expression={"$log10": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$log10 should return infinity for float infinity",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        doc={"value": DECIMAL128_INFINITY},
        expression={"$log10": ["$value"]},
        expected=DECIMAL128_INFINITY,
        msg="$log10 should return decimal128 infinity for decimal128 infinity",
    ),
]

# Property [NaN]: $log10 of NaN returns a double NaN, including for a decimal128 NaN input.
LOG10_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan",
        doc={"value": FLOAT_NAN},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log10 should return NaN for float NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        doc={"value": DECIMAL128_NAN},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$log10 should return NaN for decimal128 NaN",
    ),
]

LOG10_NON_FINITE_TESTS = LOG10_INFINITY_TESTS + LOG10_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LOG10_NON_FINITE_TESTS))
def test_log10_non_finite(collection, test_case: ExpressionTestCase):
    """Test $log10 positive infinity and NaN cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
