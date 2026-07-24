"""Tests for $floor handling of infinities and NaN across double and decimal128 inputs."""

from __future__ import annotations

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
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Infinity]: floor returns floating-point infinities unchanged, while decimal128
# infinities floor to NaN.
FLOOR_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity_float_positive",
        doc={"value": FLOAT_INFINITY},
        expression={"$floor": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$floor should return positive infinity unchanged",
    ),
    ExpressionTestCase(
        "infinity_float_negative",
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        expression={"$floor": ["$value"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$floor should return negative infinity unchanged",
    ),
    ExpressionTestCase(
        "infinity_decimal_positive",
        doc={"value": DECIMAL128_INFINITY},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$floor should return NaN for decimal128 positive infinity",
    ),
    ExpressionTestCase(
        "infinity_decimal_negative",
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$floor should return NaN for decimal128 negative infinity",
    ),
]

# Property [NaN]: floor of NaN is NaN, preserving the input's floating-point family.
FLOOR_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_float",
        doc={"value": FLOAT_NAN},
        expression={"$floor": ["$value"]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$floor should return NaN for a double NaN",
    ),
    ExpressionTestCase(
        "nan_decimal",
        doc={"value": DECIMAL128_NAN},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$floor should return NaN for a decimal128 NaN",
    ),
]

FLOOR_NAN_INFINITY_TESTS = FLOOR_INFINITY_TESTS + FLOOR_NAN_TESTS


@pytest.mark.parametrize("test", pytest_params(FLOOR_NAN_INFINITY_TESTS))
def test_floor_nan_infinity(collection, test):
    """Test $floor handling of infinities and NaN."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
