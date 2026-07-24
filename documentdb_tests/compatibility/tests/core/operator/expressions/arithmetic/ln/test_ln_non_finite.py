"""Tests for $ln of positive infinity and NaN inputs."""

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

# Property [Infinity]: $ln of positive infinity is infinity of the same type.
LN_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_infinity",
        doc={"value": FLOAT_INFINITY},
        expression={"$ln": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$ln should return infinity for float infinity",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        doc={"value": DECIMAL128_INFINITY},
        expression={"$ln": ["$value"]},
        expected=DECIMAL128_INFINITY,
        msg="$ln should return decimal128 infinity for decimal128 infinity",
    ),
]

# Property [NaN]: $ln of NaN returns a double NaN, including for a decimal128 NaN input.
LN_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan",
        doc={"value": FLOAT_NAN},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$ln should return NaN for float NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        doc={"value": DECIMAL128_NAN},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$ln should return NaN for decimal128 NaN",
    ),
]

LN_NON_FINITE_TESTS = LN_INFINITY_TESTS + LN_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LN_NON_FINITE_TESTS))
def test_ln_non_finite(collection, test_case: ExpressionTestCase):
    """Test $ln positive infinity and NaN cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
