"""$toDecimal Decimal128 passthrough tests: identity, trailing zeros, exponent, and specials."""

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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
)

# Property [Decimal128 Passthrough]: $toDecimal is the identity function for Decimal128 inputs,
# preserving trailing zeros, exponent form, sign bits, and special values exactly.
TODECIMAL_DECIMAL128_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec128_zero",
        msg="Decimal128 zero passes through unchanged",
        expression={"$toDecimal": DECIMAL128_ZERO},
        expected=DECIMAL128_ZERO,
    ),
    ExpressionTestCase(
        "dec128_negative_zero",
        msg="Decimal128 negative zero passes through preserving sign",
        expression={"$toDecimal": DECIMAL128_NEGATIVE_ZERO},
        expected=DECIMAL128_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "dec128_one",
        msg="Decimal128 1 passes through unchanged",
        expression={"$toDecimal": Decimal128("1")},
        expected=Decimal128("1"),
    ),
    ExpressionTestCase(
        "dec128_trailing_zero",
        msg="Decimal128 trailing zero (1.0) passes through preserving the trailing zero",
        expression={"$toDecimal": DECIMAL128_TRAILING_ZERO},
        expected=DECIMAL128_TRAILING_ZERO,
    ),
    ExpressionTestCase(
        "dec128_many_trailing_zeros",
        msg="Decimal128 with many trailing zeros passes through preserving all zeros",
        expression={"$toDecimal": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=DECIMAL128_MANY_TRAILING_ZEROS,
    ),
    ExpressionTestCase(
        "dec128_exponent_form",
        msg="Decimal128 in exponent form (1E+6144) passes through preserving exponent",
        expression={"$toDecimal": DECIMAL128_LARGE_EXPONENT},
        expected=DECIMAL128_LARGE_EXPONENT,
    ),
    ExpressionTestCase(
        "dec128_negative",
        msg="Decimal128 negative value passes through unchanged",
        expression={"$toDecimal": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=DECIMAL128_NEGATIVE_ONE_AND_HALF,
    ),
    ExpressionTestCase(
        "dec128_max",
        msg="Decimal128 max value passes through unchanged",
        expression={"$toDecimal": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
    ),
    ExpressionTestCase(
        "dec128_min",
        msg="Decimal128 min value passes through unchanged",
        expression={"$toDecimal": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
    ),
    ExpressionTestCase(
        "dec128_min_positive",
        msg="Decimal128 min positive value (1E-6176) passes through unchanged",
        expression={"$toDecimal": DECIMAL128_MIN_POSITIVE},
        expected=DECIMAL128_MIN_POSITIVE,
    ),
    ExpressionTestCase(
        "dec128_max_negative",
        msg="Decimal128 max negative value (-1E-6176) passes through unchanged",
        expression={"$toDecimal": DECIMAL128_MAX_NEGATIVE},
        expected=DECIMAL128_MAX_NEGATIVE,
    ),
    ExpressionTestCase(
        "dec128_nan",
        msg="Decimal128 NaN passes through unchanged",
        expression={"$toDecimal": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
    ),
    ExpressionTestCase(
        "dec128_negative_nan",
        msg="Decimal128 -NaN passes through preserving sign bit",
        expression={"$toDecimal": DECIMAL128_NEGATIVE_NAN},
        expected=DECIMAL128_NEGATIVE_NAN,
    ),
    ExpressionTestCase(
        "dec128_infinity",
        msg="Decimal128 Infinity passes through unchanged",
        expression={"$toDecimal": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
    ),
    ExpressionTestCase(
        "dec128_negative_infinity",
        msg="Decimal128 -Infinity passes through unchanged",
        expression={"$toDecimal": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "dec128_high_precision",
        msg="Decimal128 maximum 34-digit coefficient passes through at full precision",
        expression={"$toDecimal": DECIMAL128_MAX_COEFFICIENT},
        expected=DECIMAL128_MAX_COEFFICIENT,
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TODECIMAL_DECIMAL128_TESTS, "$toDecimal", "decimal")),
)
def test_toDecimal_decimal128(collection, test: ExpressionTestCase):
    """$toDecimal is the identity function for Decimal128 inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
