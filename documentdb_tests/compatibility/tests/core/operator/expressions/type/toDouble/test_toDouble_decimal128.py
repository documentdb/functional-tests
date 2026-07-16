"""$toDouble Decimal128 conversion tests: zeros, infinity, precision, and overflow."""

import pytest
from bson import Decimal128

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
    DECIMAL128_INFINITY,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Decimal128]: $toDouble converts Decimal128 values to double, mapping signed zeros
# and infinities correctly, and rejecting values outside the double range.
TODOUBLE_DECIMAL128_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec128_zero",
        msg="Decimal128 zero converts to 0.0",
        expression={"$toDouble": DECIMAL128_ZERO},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "dec128_neg_zero",
        msg="Decimal128 -0 converts to -0.0 preserving sign",
        expression={"$toDouble": DECIMAL128_NEGATIVE_ZERO},
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "dec128_inf",
        msg="Decimal128 Infinity converts to +Inf",
        expression={"$toDouble": DECIMAL128_INFINITY},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "dec128_neg_inf",
        msg="Decimal128 -Infinity converts to -Inf",
        expression={"$toDouble": DECIMAL128_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "dec128_one",
        msg="Decimal128 1 converts to 1.0",
        expression={"$toDouble": Decimal128("1")},
        expected=1.0,
    ),
    ExpressionTestCase(
        "dec128_trailing_zero",
        msg="Decimal128 trailing zero normalizes correctly",
        expression={"$toDouble": DECIMAL128_TRAILING_ZERO},
        expected=1.0,
    ),
    ExpressionTestCase(
        "dec128_many_trailing_zeros",
        msg="Decimal128 with many trailing zeros normalizes correctly",
        expression={"$toDouble": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=1.0,
    ),
    ExpressionTestCase(
        "dec128_neg",
        msg="Decimal128 negative value converts correctly",
        expression={"$toDouble": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=DOUBLE_NEGATIVE_ONE_AND_HALF,
    ),
    ExpressionTestCase(
        "dec128_overflow",
        msg="Decimal128 value exceeding double max is a conversion failure",
        expression={"$toDouble": DECIMAL128_MAX},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "dec128_neg_overflow",
        msg="Decimal128 most-negative value exceeding double range is a conversion failure",
        expression={"$toDouble": DECIMAL128_MIN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_DECIMAL128_TESTS))
def test_toDouble_decimal128(collection, test: ExpressionTestCase):
    """$toDouble converts Decimal128 values including infinity, signed zero, and overflow."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
