"""$toDecimal valid string conversion tests: decimal, scientific notation, and special values."""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [String Conversion — Valid]: base-10 numeric strings, scientific notation, and
# special value strings convert to the corresponding Decimal128.
TODECIMAL_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_negative_decimal",
        msg="$toDecimal should convert negative decimal string",
        expression={"$toDecimal": "-5.5"},
        expected=Decimal128("-5.5"),
    ),
    ExpressionTestCase(
        "str_scientific_upper",
        msg="$toDecimal should accept uppercase E in scientific notation",
        expression={"$toDecimal": "1.5E+3"},
        expected=Decimal128("1.5E+3"),
    ),
    ExpressionTestCase(
        "str_scientific_lower",
        msg="$toDecimal should accept lowercase e in scientific notation",
        expression={"$toDecimal": "1.5e+3"},
        expected=Decimal128("1.5E+3"),
    ),
    ExpressionTestCase(
        "str_leading_plus",
        msg="$toDecimal should strip leading plus sign",
        expression={"$toDecimal": "+123"},
        expected=Decimal128("123"),
    ),
    ExpressionTestCase(
        "str_leading_zeros",
        msg="$toDecimal should strip leading zeros",
        expression={"$toDecimal": "007"},
        expected=Decimal128("7"),
    ),
    ExpressionTestCase(
        "str_leading_decimal",
        msg="$toDecimal should accept leading decimal point",
        expression={"$toDecimal": ".5"},
        expected=DECIMAL128_HALF,
    ),
    ExpressionTestCase(
        "str_trailing_decimal",
        msg="$toDecimal should accept trailing decimal point",
        expression={"$toDecimal": "5."},
        expected=Decimal128("5"),
    ),
    ExpressionTestCase(
        "str_trailing_zeros_preserved",
        msg="$toDecimal should preserve trailing zeros in string decimal part",
        expression={"$toDecimal": "1.00"},
        expected=Decimal128("1.00"),
    ),
    ExpressionTestCase(
        "str_nan_mixed_case",
        msg="$toDecimal should accept 'NaN'",
        expression={"$toDecimal": "NaN"},
        expected=DECIMAL128_NAN,
    ),
    ExpressionTestCase(
        "str_nan_lower",
        msg="$toDecimal should accept 'nan' case-insensitively",
        expression={"$toDecimal": "nan"},
        expected=DECIMAL128_NAN,
    ),
    ExpressionTestCase(
        "str_nan_upper",
        msg="$toDecimal should accept 'NAN' case-insensitively",
        expression={"$toDecimal": "NAN"},
        expected=DECIMAL128_NAN,
    ),
    ExpressionTestCase(
        "str_infinity",
        msg="$toDecimal should accept 'Infinity'",
        expression={"$toDecimal": "Infinity"},
        expected=DECIMAL128_INFINITY,
    ),
    ExpressionTestCase(
        "str_inf_short",
        msg="$toDecimal should accept 'inf' short form",
        expression={"$toDecimal": "inf"},
        expected=DECIMAL128_INFINITY,
    ),
    ExpressionTestCase(
        "str_inf_upper",
        msg="$toDecimal should accept 'INF' case-insensitively",
        expression={"$toDecimal": "INF"},
        expected=DECIMAL128_INFINITY,
    ),
    ExpressionTestCase(
        "str_neg_nan",
        msg="$toDecimal should convert '-NaN' string preserving sign bit",
        expression={"$toDecimal": "-NaN"},
        expected=Decimal128("-NaN"),
    ),
    ExpressionTestCase(
        "str_neg_infinity",
        msg="$toDecimal should preserve sign on negative Infinity string",
        expression={"$toDecimal": "-Infinity"},
        expected=DECIMAL128_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "str_plus_infinity",
        msg="$toDecimal should strip plus sign from Infinity string",
        expression={"$toDecimal": "+Infinity"},
        expected=DECIMAL128_INFINITY,
    ),
    ExpressionTestCase(
        "str_max_exponent",
        msg="$toDecimal should accept maximum exponent string",
        expression={"$toDecimal": "1E+6144"},
        expected=Decimal128("1.000000000000000000000000000000000E+6144"),
    ),
    ExpressionTestCase(
        "str_min_exponent",
        msg="$toDecimal should accept minimum exponent string",
        expression={"$toDecimal": "1E-6176"},
        expected=DECIMAL128_MIN_POSITIVE,
    ),
    ExpressionTestCase(
        "str_exactly_34_digits",
        msg="$toDecimal should convert 34-digit string without rounding",
        expression={"$toDecimal": "1234567890123456789012345678901234"},
        expected=Decimal128("1234567890123456789012345678901234"),
    ),
    ExpressionTestCase(
        "str_exceeds_34_digits",
        msg="$toDecimal should round strings exceeding 34 significant digits",
        expression={"$toDecimal": "12345678901234567890123456789012345"},
        expected=Decimal128("1.234567890123456789012345678901234E+34"),
    ),
    ExpressionTestCase(
        "str_negative_zero",
        msg="$toDecimal should preserve negative zero from string",
        expression={"$toDecimal": "-0"},
        expected=DECIMAL128_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "str_plus_zero",
        msg="$toDecimal should convert '+0' to Decimal128 zero",
        expression={"$toDecimal": "+0"},
        expected=DECIMAL128_ZERO,
    ),
    ExpressionTestCase(
        "str_plus_dot_zero",
        msg="$toDecimal should convert '+.0' to Decimal128 zero",
        expression={"$toDecimal": "+.0"},
        expected=Decimal128("0.0"),
    ),
    ExpressionTestCase(
        "str_neg_zero_neg_exp",
        msg="$toDecimal should convert '-0E-1' preserving negative zero",
        expression={"$toDecimal": "-0E-1"},
        expected=Decimal128("-0.0"),
    ),
    ExpressionTestCase(
        "str_zero_pos_exp",
        msg="$toDecimal should convert '0E+1' preserving exponent",
        expression={"$toDecimal": "0E+1"},
        expected=Decimal128("0E+1"),
    ),
    ExpressionTestCase(
        "str_shifted_decimal_large",
        msg="$toDecimal should convert shifted decimal form of large value",
        expression={"$toDecimal": ".1797693134862315807E+309"},
        expected=Decimal128("1.797693134862315807E+308"),
    ),
    ExpressionTestCase(
        "str_plus_prefixed_max",
        msg="$toDecimal should strip plus sign from max-range string",
        expression={"$toDecimal": "+1.797693134862315807E+308"},
        expected=Decimal128("1.797693134862315807E+308"),
    ),
    ExpressionTestCase(
        "str_rounding_34_digits",
        msg="$toDecimal rounds at digit 35; digit-35 is 0 so result rounds down",
        expression={"$toDecimal": "1.00000000000000000000000000000000099999"},
        expected=Decimal128("1.000000000000000000000000000000000"),
    ),
]


# Property [String Size Limit — Valid]: a valid numeric string one byte under the limit converts.
TODECIMAL_STRING_SIZE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_one_under_valid",
        msg="Valid numeric string one byte under limit converts successfully",
        expression=lazy(lambda: {"$toDecimal": "0" * (STRING_SIZE_LIMIT_BYTES - 2) + "1"}),
        expected=Decimal128("1"),
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TODECIMAL_STRING_TESTS + TODECIMAL_STRING_SIZE_LIMIT_TESTS)
)
def test_toDecimal_string(collection, test: ExpressionTestCase):
    """$toDecimal parses valid numeric strings including scientific notation and special values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
