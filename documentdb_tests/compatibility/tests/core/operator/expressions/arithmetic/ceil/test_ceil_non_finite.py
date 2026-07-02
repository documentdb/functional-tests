"""Tests for $ceil with infinity and NaN inputs for double and decimal128 types."""

import math

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

# Property [Infinity]: $ceil of positive or negative float infinity returns the same infinity.
# $ceil of decimal128 infinity returns NaN (overflow during rounding).
CEIL_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_infinity",
        doc={"value": FLOAT_INFINITY},
        expression={"$ceil": ["$value"]},
        expected=FLOAT_INFINITY,
        msg="$ceil should return float infinity for float infinity",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        expression={"$ceil": ["$value"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$ceil should return float negative infinity for float negative infinity",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        doc={"value": DECIMAL128_INFINITY},
        expression={"$ceil": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$ceil should return NaN for decimal128 infinity",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$ceil": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$ceil should return NaN for decimal128 negative infinity",
    ),
]

# Property [NaN]: $ceil of NaN returns NaN of the same type.
CEIL_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan",
        doc={"value": FLOAT_NAN},
        expression={"$ceil": ["$value"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$ceil should return NaN for float NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        doc={"value": DECIMAL128_NAN},
        expression={"$ceil": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$ceil should return NaN for decimal128 NaN",
    ),
]

CEIL_NON_FINITE_TESTS = CEIL_INFINITY_TESTS + CEIL_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CEIL_NON_FINITE_TESTS))
def test_ceil_non_finite(collection, test_case: ExpressionTestCase):
    """Test $ceil infinity and NaN cases for double and decimal128."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
