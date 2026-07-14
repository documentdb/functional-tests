"""$toInt string conversion tests: valid base-10 integers and rejection of invalid strings."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR, STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [String Conversion]: a base-10 integer string within int32 range converts to the
# corresponding int32 value; leading zeros, a leading '+', and a leading '-' are accepted.
TOINT_STRING_VALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_zero",
        msg="'0' converts to 0",
        expression={"$toInt": "0"},
        expected=INT32_ZERO,
    ),
    ExpressionTestCase(
        "str_positive",
        msg="'42' converts to 42",
        expression={"$toInt": "42"},
        expected=42,
    ),
    ExpressionTestCase(
        "str_negative",
        msg="'-2' converts to -2",
        expression={"$toInt": "-2"},
        expected=-2,
    ),
    ExpressionTestCase(
        "str_plus_sign",
        msg="'+1' accepts leading + sign",
        expression={"$toInt": "+1"},
        expected=1,
    ),
    ExpressionTestCase(
        "str_leading_zeros",
        msg="'007' strips leading zeros",
        expression={"$toInt": "007"},
        expected=7,
    ),
    ExpressionTestCase(
        "str_plus_leading_zeros",
        msg="'+0042' accepts + sign with leading zeros",
        expression={"$toInt": "+0042"},
        expected=42,
    ),
    ExpressionTestCase(
        "str_minus_leading_zeros",
        msg="'-0042' accepts - sign with leading zeros",
        expression={"$toInt": "-0042"},
        expected=-42,
    ),
    ExpressionTestCase(
        "str_thousands_leading_zeros",
        msg="Thousands of leading zeros with trailing '1' converts to 1",
        expression={"$toInt": "0" * 10_000 + "1"},
        expected=1,
    ),
    ExpressionTestCase(
        "str_minus_zero",
        msg="'-0' converts to 0",
        expression={"$toInt": "-0"},
        expected=INT32_ZERO,
    ),
    ExpressionTestCase(
        "str_plus_zero",
        msg="'+0' converts to 0",
        expression={"$toInt": "+0"},
        expected=INT32_ZERO,
    ),
    ExpressionTestCase(
        "str_int32_max",
        msg="'2147483647' (int32 max as string) converts exactly",
        expression={"$toInt": "2147483647"},
        expected=INT32_MAX,
    ),
    ExpressionTestCase(
        "str_int32_min",
        msg="'-2147483648' (int32 min as string) converts exactly",
        expression={"$toInt": "-2147483648"},
        expected=INT32_MIN,
    ),
]

# Property [String Errors]: strings that are not valid base-10 integers within int32 range
# produce a conversion failure.
TOINT_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_err_empty",
        msg="Empty string is a conversion failure",
        expression={"$toInt": ""},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_alpha",
        msg="Alphabetic string is a conversion failure",
        expression={"$toInt": "a"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_decimal_point",
        msg="'3.14' (decimal point) is a conversion failure",
        expression={"$toInt": "3.14"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_decimal_zero_fraction",
        msg="'1.0' (fractional part is zero) is still a conversion failure",
        expression={"$toInt": "1.0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_trailing_dot",
        msg="'1.' (trailing dot) is a conversion failure",
        expression={"$toInt": "1."},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_leading_dot",
        msg="'.1' (leading dot) is a conversion failure",
        expression={"$toInt": ".1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_sci_lower",
        msg="'1e2' (scientific notation lowercase) is a conversion failure",
        expression={"$toInt": "1e2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_sci_upper",
        msg="'1E2' (scientific notation uppercase) is a conversion failure",
        expression={"$toInt": "1E2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_hex_lower",
        msg="'0x0' (lowercase hex prefix) is a conversion failure",
        expression={"$toInt": "0x0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_hex_upper",
        msg="'0X0' (uppercase hex prefix) is a conversion failure",
        expression={"$toInt": "0X0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_nan",
        msg="'NaN' is a conversion failure",
        expression={"$toInt": "NaN"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_infinity",
        msg="'Infinity' is a conversion failure",
        expression={"$toInt": "Infinity"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_inf",
        msg="'inf' is a conversion failure",
        expression={"$toInt": "inf"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_true",
        msg="'true' is a conversion failure",
        expression={"$toInt": "true"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_false",
        msg="'false' is a conversion failure",
        expression={"$toInt": "false"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_null_word",
        msg="'null' is a conversion failure",
        expression={"$toInt": "null"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_leading_space",
        msg="Leading whitespace is a conversion failure",
        expression={"$toInt": " 1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_trailing_space",
        msg="Trailing whitespace is a conversion failure",
        expression={"$toInt": "1 "},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_embedded_space",
        msg="Embedded whitespace is a conversion failure",
        expression={"$toInt": "1 2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_tab",
        msg="Tab character is a conversion failure",
        expression={"$toInt": "\t1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_newline",
        msg="Newline character is a conversion failure",
        expression={"$toInt": "1\n"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_carriage_return",
        msg="Carriage return character is a conversion failure",
        expression={"$toInt": "1\r"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_nbsp",
        msg="U+00A0 NBSP character is a conversion failure",
        expression={"$toInt": "\u00a01"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_en_space",
        msg="U+2000 EN SPACE character is a conversion failure",
        expression={"$toInt": "\u20001"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_em_space",
        msg="U+2003 EM SPACE character is a conversion failure",
        expression={"$toInt": "\u20031"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_bom",
        msg="U+FEFF BOM character is a conversion failure",
        expression={"$toInt": "\ufeff1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_zwsp",
        msg="U+200B ZWSP character is a conversion failure",
        expression={"$toInt": "\u200b1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_zwj",
        msg="U+200D ZWJ character is a conversion failure",
        expression={"$toInt": "\u200d1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_ltr_mark",
        msg="U+200E LTR mark character is a conversion failure",
        expression={"$toInt": "\u200e1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_rtl_mark",
        msg="U+200F RTL mark character is a conversion failure",
        expression={"$toInt": "\u200f1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_fullwidth_digit",
        msg="U+FF11 fullwidth digit one is a conversion failure",
        expression={"$toInt": "\uff11"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_arabic_indic_digit",
        msg="U+0661 Arabic-Indic digit one is a conversion failure",
        expression={"$toInt": "\u0661"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_superscript_digit",
        msg="U+00B2 superscript two is a conversion failure",
        expression={"$toInt": "\u00b2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_null_byte",
        msg="String with null byte is a conversion failure",
        expression={"$toInt": "\x001"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_control_char",
        msg="String with control character is a conversion failure",
        expression={"$toInt": "\x011"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_special_chars",
        msg="String with special characters is a conversion failure",
        expression={"$toInt": "!@#$%^&*()"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_backslash",
        msg="String with backslash is a conversion failure",
        expression={"$toInt": "\\1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_braces",
        msg="String with braces is a conversion failure",
        expression={"$toInt": "{1}"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_brackets",
        msg="String with brackets is a conversion failure",
        expression={"$toInt": "[1]"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_quotes",
        msg="String with quotes ('\"') is a conversion failure",
        expression={"$toInt": '"1"'},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_sign_only_plus",
        msg="Sign-only string '+' is a conversion failure",
        expression={"$toInt": "+"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_sign_only_minus",
        msg="Sign-only string '-' is a conversion failure",
        expression={"$toInt": "-"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_double_minus",
        msg="Double-sign string '--1' is a conversion failure",
        expression={"$toInt": "--1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_double_plus",
        msg="Double-sign string '++1' is a conversion failure",
        expression={"$toInt": "++1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_mixed_signs",
        msg="Mixed-sign string '+-1' is a conversion failure",
        expression={"$toInt": "+-1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_comma_separator",
        msg="String with comma separator '1,000' is a conversion failure",
        expression={"$toInt": "1,000"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_underscore_separator",
        msg="String with underscore separator '1_000' is a conversion failure",
        expression={"$toInt": "1_000"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_overflow_above_max",
        msg="'2147483648' (one above int32 max) is a conversion failure",
        expression={"$toInt": "2147483648"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_overflow_below_min",
        msg="'-2147483649' (one below int32 min) is a conversion failure",
        expression={"$toInt": "-2147483649"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_overflow_very_large",
        msg="Very large numeric string is a conversion failure",
        expression={"$toInt": "9" * 100},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_zwj_emoji",
        msg="ZWJ emoji sequence is a conversion failure",
        expression={"$toInt": "\U0001f468\u200d\U0001f469\u200d\U0001f467"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_literal_dollar_number",
        msg="'$42' passed via $literal is a conversion failure",
        expression={"$toInt": {"$literal": "$42"}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_literal_double_dollar_number",
        msg="'$$42' passed via $literal is a conversion failure",
        expression={"$toInt": {"$literal": "$$42"}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_literal_dollar_only",
        msg="'$' passed via $literal is a conversion failure",
        expression={"$toInt": {"$literal": "$"}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_literal_double_dollar_only",
        msg="'$$' passed via $literal is a conversion failure",
        expression={"$toInt": {"$literal": "$$"}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOINT_STRING_TESTS = TOINT_STRING_VALID_TESTS + TOINT_STRING_ERROR_TESTS


# Property [String Size Limit]: $toInt checks the byte length of string inputs before
# attempting conversion; strings at or above the limit are rejected unconditionally.
TOINT_STRING_SIZE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_one_under_valid",
        msg="Valid integer string one byte under limit converts successfully",
        expression=lazy(lambda: {"$toInt": "0" * (STRING_SIZE_LIMIT_BYTES - 2) + "1"}),
        expected=1,
    ),
    ExpressionTestCase(
        "size_one_under_non_numeric",
        msg="Non-numeric string one byte under limit passes size check but fails conversion",
        expression=lazy(lambda: {"$toInt": "a" * (STRING_SIZE_LIMIT_BYTES - 1)}),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit",
        msg="String at STRING_SIZE_LIMIT_BYTES is rejected with STRING_SIZE_LIMIT_ERROR",
        expression=lazy(lambda: {"$toInt": "a" * STRING_SIZE_LIMIT_BYTES}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit_four_byte",
        msg="4-byte character string reaching STRING_SIZE_LIMIT_BYTES is rejected",
        expression=lazy(lambda: {"$toInt": "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TOINT_STRING_TESTS + TOINT_STRING_SIZE_LIMIT_TESTS))
def test_toInt_string(collection, test: ExpressionTestCase):
    """$toInt parses valid base-10 integer strings and rejects malformed or out-of-range ones."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
