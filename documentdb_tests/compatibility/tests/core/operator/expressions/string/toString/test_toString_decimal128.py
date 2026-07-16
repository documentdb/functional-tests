"""$toString Decimal128 conversion tests: precision, trailing zeros, exponents, and specials."""

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
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
)

# Property [Decimal128 Conversion]: Decimal128 values convert to their canonical string
# representation, preserving trailing zeros, signed zeros, and exponent form.
TOSTRING_DECIMAL128_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_plain_one",
        msg="Decimal128 one converts to '1'",
        expression={"$toString": Decimal128("1")},
        expected="1",
    ),
    ExpressionTestCase(
        "decimal_plain_zero",
        msg="Decimal128 zero converts to '0'",
        expression={"$toString": DECIMAL128_ZERO},
        expected="0",
    ),
    ExpressionTestCase(
        "decimal_negative",
        msg="Negative Decimal128 converts correctly",
        expression={"$toString": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected="-1.5",
    ),
    ExpressionTestCase(
        "decimal_trailing_one_zero",
        msg="Decimal128 with one trailing zero preserves it",
        expression={"$toString": DECIMAL128_TRAILING_ZERO},
        expected="1.0",
    ),
    ExpressionTestCase(
        "decimal_trailing_two_zeros",
        msg="Decimal128 with two trailing zeros preserves them",
        expression={"$toString": Decimal128("1.00")},
        expected="1.00",
    ),
    ExpressionTestCase(
        "decimal_trailing_max_zeros",
        msg="Decimal128 with maximum trailing zeros preserves all 33",
        expression={"$toString": Decimal128("1.000000000000000000000000000000000")},
        expected="1.000000000000000000000000000000000",
    ),
    ExpressionTestCase(
        "decimal_neg_zero",
        msg="Decimal128 negative zero converts to '-0'",
        expression={"$toString": DECIMAL128_NEGATIVE_ZERO},
        expected="-0",
    ),
    ExpressionTestCase(
        "decimal_neg_zero_trailing",
        msg="Decimal128 negative zero with trailing zero preserves form",
        expression={"$toString": Decimal128("-0.0")},
        expected="-0.0",
    ),
    ExpressionTestCase(
        "decimal_neg_zero_two_trailing",
        msg="Decimal128 negative zero with two trailing zeros preserves form",
        expression={"$toString": Decimal128("-0.00")},
        expected="-0.00",
    ),
    ExpressionTestCase(
        "decimal_neg_zero_exp",
        msg="Decimal128 negative zero with exponent preserves form",
        expression={"$toString": Decimal128("-0E+10")},
        expected="-0E+10",
    ),
    ExpressionTestCase(
        "decimal_sci_pos_exp",
        msg="Decimal128 uses uppercase E for positive exponent",
        expression={"$toString": Decimal128("1E+10")},
        expected="1E+10",
    ),
    ExpressionTestCase(
        "decimal_sci_neg_exp",
        msg="Decimal128 uses uppercase E for negative exponent",
        expression={"$toString": Decimal128("1E-10")},
        expected="1E-10",
    ),
    ExpressionTestCase(
        "decimal_nan",
        msg="Decimal128 NaN converts to 'NaN'",
        expression={"$toString": Decimal128("NaN")},
        expected="NaN",
    ),
    ExpressionTestCase(
        "decimal_snan",
        msg="Decimal128 sNaN normalizes to 'NaN'",
        expression={"$toString": Decimal128("sNaN")},
        expected="NaN",
    ),
    ExpressionTestCase(
        "decimal_neg_nan",
        msg="Decimal128 -NaN normalizes to 'NaN'",
        expression={"$toString": Decimal128("-NaN")},
        expected="NaN",
    ),
    ExpressionTestCase(
        "decimal_neg_snan",
        msg="Decimal128 -sNaN normalizes to 'NaN'",
        expression={"$toString": Decimal128("-sNaN")},
        expected="NaN",
    ),
    ExpressionTestCase(
        "decimal_pos_infinity",
        msg="Decimal128 Infinity converts to 'Infinity'",
        expression={"$toString": DECIMAL128_INFINITY},
        expected="Infinity",
    ),
    ExpressionTestCase(
        "decimal_neg_infinity",
        msg="Decimal128 -Infinity converts to '-Infinity'",
        expression={"$toString": DECIMAL128_NEGATIVE_INFINITY},
        expected="-Infinity",
    ),
    ExpressionTestCase(
        "decimal_max_precision",
        msg="Decimal128 with 34 significant digits preserves full precision",
        expression={"$toString": Decimal128("1234567890123456789012345678901234")},
        expected="1234567890123456789012345678901234",
    ),
    ExpressionTestCase(
        "decimal_max_precision_fractional",
        msg="Decimal128 with 34 significant digits and decimal point preserves all",
        expression={"$toString": Decimal128("9.876543210987654321098765432109876")},
        expected="9.876543210987654321098765432109876",
    ),
    ExpressionTestCase(
        "decimal_max_value",
        msg="Decimal128 max value converts to its canonical form",
        expression={"$toString": DECIMAL128_MAX},
        expected="9.999999999999999999999999999999999E+6144",
    ),
    ExpressionTestCase(
        "decimal_min_exp",
        msg="Decimal128 minimum positive exponent converts correctly",
        expression={"$toString": DECIMAL128_MIN_POSITIVE},
        expected="1E-6176",
    ),
    ExpressionTestCase(
        "decimal_max_negative",
        msg="Decimal128 most-negative-exponent value converts correctly",
        expression={"$toString": DECIMAL128_MAX_NEGATIVE},
        expected="-1E-6176",
    ),
    ExpressionTestCase(
        "decimal_max_exp",
        msg="Decimal128 large positive exponent expands to full 34-digit precision",
        expression={"$toString": DECIMAL128_LARGE_EXPONENT},
        expected="1.000000000000000000000000000000000E+6144",
    ),
    ExpressionTestCase(
        "decimal_zero_pos_exp",
        msg="Decimal128 zero with positive exponent preserves form",
        expression={"$toString": Decimal128("0E+10")},
        expected="0E+10",
    ),
    ExpressionTestCase(
        "decimal_zero_neg_exp",
        msg="Decimal128 zero with negative exponent preserves form",
        expression={"$toString": Decimal128("0E-10")},
        expected="0E-10",
    ),
    ExpressionTestCase(
        "decimal_normalized_100",
        msg="Decimal128 1.00E+2 normalizes to '100'",
        expression={"$toString": Decimal128("1.00E+2")},
        expected="100",
    ),
    ExpressionTestCase(
        "decimal_normalized_10",
        msg="Decimal128 1.0E+1 normalizes to '10'",
        expression={"$toString": Decimal128("1.0E+1")},
        expected="10",
    ),
    ExpressionTestCase(
        "decimal_small_exp_normalized",
        msg="Decimal128 3E-5 normalizes to decimal notation '0.00003'",
        expression={"$toString": Decimal128("3E-5")},
        expected="0.00003",
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOSTRING_DECIMAL128_TESTS, "$toString", "string")),
)
def test_toString_decimal128(collection, test: ExpressionTestCase):
    """$toString converts Decimal128 values to their canonical string representation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
