"""$toInt Decimal128 conversion tests: truncation, boundary values, and overflow."""

import pytest
from bson import Decimal128

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
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
)

# Property [Decimal128 Truncation]: $toInt truncates Decimal128 toward zero.
TOINT_DECIMAL128_TRUNCATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec128_zero",
        msg="Decimal128 zero converts to 0",
        expression={"$toInt": DECIMAL128_ZERO},
        expected=INT32_ZERO,
    ),
    ExpressionTestCase(
        "dec128_neg_zero",
        msg="Decimal128 -0 converts to 0",
        expression={"$toInt": DECIMAL128_NEGATIVE_ZERO},
        expected=INT32_ZERO,
    ),
    ExpressionTestCase(
        "dec128_one",
        msg="Decimal128 1 converts to 1",
        expression={"$toInt": Decimal128("1")},
        expected=1,
    ),
    ExpressionTestCase(
        "dec128_neg_one",
        msg="Decimal128 -1 converts to -1",
        expression={"$toInt": Decimal128("-1")},
        expected=-1,
    ),
    ExpressionTestCase(
        "dec128_truncate_positive",
        msg="Decimal128 1.9 is truncated toward zero to 1",
        expression={"$toInt": Decimal128("1.9")},
        expected=1,
    ),
    ExpressionTestCase(
        "dec128_truncate_negative",
        msg="Decimal128 -1.9 is truncated toward zero to -1",
        expression={"$toInt": Decimal128("-1.9")},
        expected=-1,
    ),
    ExpressionTestCase(
        "dec128_trailing_zero",
        msg="Decimal128 1.0 (trailing zero) converts to 1",
        expression={"$toInt": DECIMAL128_TRAILING_ZERO},
        expected=1,
    ),
]

# Property [Decimal128 Boundary]: $toInt accepts Decimal128 values in the int32 range;
# rejects NaN, infinity, and out-of-range values.
TOINT_DECIMAL128_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec128_int32_max",
        msg="Decimal128 equal to int32 max converts exactly",
        expression={"$toInt": Decimal128(str(INT32_MAX))},
        expected=INT32_MAX,
    ),
    ExpressionTestCase(
        "dec128_int32_min",
        msg="Decimal128 equal to int32 min converts exactly",
        expression={"$toInt": Decimal128(str(INT32_MIN))},
        expected=INT32_MIN,
    ),
    ExpressionTestCase(
        "dec128_overflow",
        msg="Decimal128 one above int32 max is a conversion failure",
        expression={"$toInt": Decimal128(str(INT32_MAX + 1))},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "dec128_underflow",
        msg="Decimal128 one below int32 min is a conversion failure",
        expression={"$toInt": Decimal128(str(INT32_MIN - 1))},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "dec128_nan",
        msg="Decimal128 NaN is a conversion failure",
        expression={"$toInt": DECIMAL128_NAN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "dec128_inf",
        msg="Decimal128 Infinity is a conversion failure",
        expression={"$toInt": DECIMAL128_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "dec128_neg_inf",
        msg="Decimal128 -Infinity is a conversion failure",
        expression={"$toInt": DECIMAL128_NEGATIVE_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOINT_DECIMAL128_TESTS = TOINT_DECIMAL128_TRUNCATION_TESTS + TOINT_DECIMAL128_BOUNDARY_TESTS


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOINT_DECIMAL128_TESTS, "$toInt", "int")),
)
def test_toInt_decimal128(collection, test: ExpressionTestCase):
    """$toInt converts Decimal128 values within int32 range; rejects NaN, infinity, and overflow."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
