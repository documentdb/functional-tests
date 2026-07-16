"""$toLong string conversion tests: valid integer strings, invalid formats, and size limit."""

import pytest
from bson import Int64

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
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [String Conversion]: base-10 integer strings with optional leading sign and leading
# zeros convert to the corresponding Int64 value.
TOLONG_STRING_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_positive",
        msg="Positive integer string converts to Int64",
        expression={"$toLong": "42"},
        expected=Int64(42),
    ),
    ExpressionTestCase(
        "str_negative",
        msg="Negative integer string converts to Int64",
        expression={"$toLong": "-2"},
        expected=Int64(-2),
    ),
    ExpressionTestCase(
        "str_zero",
        msg="'0' converts to Int64(0)",
        expression={"$toLong": "0"},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "str_leading_plus",
        msg="Leading '+' sign is accepted",
        expression={"$toLong": "+5"},
        expected=Int64(5),
    ),
    ExpressionTestCase(
        "str_leading_zeros",
        msg="Leading zeros are accepted",
        expression={"$toLong": "007"},
        expected=Int64(7),
    ),
    ExpressionTestCase(
        "str_plus_leading_zeros",
        msg="'+' sign with leading zeros is accepted",
        expression={"$toLong": "+0042"},
        expected=Int64(42),
    ),
    ExpressionTestCase(
        "str_minus_leading_zeros",
        msg="'-' sign with leading zeros is accepted",
        expression={"$toLong": "-0042"},
        expected=Int64(-42),
    ),
    ExpressionTestCase(
        "str_negative_zero",
        msg="'-0' converts to Int64(0)",
        expression={"$toLong": "-0"},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "str_plus_zero",
        msg="'+0' converts to Int64(0)",
        expression={"$toLong": "+0"},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "str_int64_max",
        msg="int64 max string converts to Int64 max",
        expression={"$toLong": "9223372036854775807"},
        expected=INT64_MAX,
    ),
    ExpressionTestCase(
        "str_int64_min",
        msg="int64 min string converts to Int64 min",
        expression={"$toLong": "-9223372036854775808"},
        expected=INT64_MIN,
    ),
]

# Property [String Conversion Errors]: non-integer string formats, decimal points, scientific
# notation, hex, whitespace, Unicode non-ASCII digits, control characters, special characters,
# sign-only strings, separator characters, and overflow strings produce a conversion error.
TOLONG_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_err_empty",
        msg="Empty string is a conversion failure",
        expression={"$toLong": ""},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_alpha",
        msg="Alphabetic string is a conversion failure",
        expression={"$toLong": "a"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_decimal_point",
        msg="String with decimal point is a conversion failure",
        expression={"$toLong": "3.0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_trailing_dot",
        msg="String with trailing decimal point is a conversion failure",
        expression={"$toLong": "1."},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_leading_dot",
        msg="String with leading decimal point is a conversion failure",
        expression={"$toLong": ".1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_sci_lower",
        msg="Lowercase scientific notation string is a conversion failure",
        expression={"$toLong": "1e2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_sci_upper",
        msg="Uppercase scientific notation string is a conversion failure",
        expression={"$toLong": "1E2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_hex_lower",
        msg="Lowercase hex prefix string is a conversion failure",
        expression={"$toLong": "0x1A"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_hex_upper",
        msg="Uppercase hex prefix string is a conversion failure",
        expression={"$toLong": "0X1A"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_nan",
        msg="'NaN' string is a conversion failure",
        expression={"$toLong": "NaN"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_infinity",
        msg="'Infinity' string is a conversion failure",
        expression={"$toLong": "Infinity"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_inf",
        msg="'inf' string is a conversion failure",
        expression={"$toLong": "inf"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_true",
        msg="'true' string is a conversion failure",
        expression={"$toLong": "true"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_false",
        msg="'false' string is a conversion failure",
        expression={"$toLong": "false"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_null",
        msg="'null' string is a conversion failure",
        expression={"$toLong": "null"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_leading_space",
        msg="String with leading space is a conversion failure",
        expression={"$toLong": " 1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_trailing_space",
        msg="String with trailing space is a conversion failure",
        expression={"$toLong": "1 "},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_embedded_space",
        msg="String with embedded space is a conversion failure",
        expression={"$toLong": "1 2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_tab",
        msg="String with tab character is a conversion failure",
        expression={"$toLong": "\t1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_newline",
        msg="String with newline is a conversion failure",
        expression={"$toLong": "1\n"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_nbsp",
        msg="String with NBSP (U+00A0) is a conversion failure",
        expression={"$toLong": "1\u00a0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_fullwidth_digit",
        msg="Fullwidth digit (U+FF11) is a conversion failure",
        expression={"$toLong": "\uff11"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_arabic_indic_digit",
        msg="Arabic-Indic digit (U+0661) is a conversion failure",
        expression={"$toLong": "\u0661"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_null_byte",
        msg="String with null byte is a conversion failure",
        expression={"$toLong": "\x001"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_plus_only",
        msg="Sign-only string '+' is a conversion failure",
        expression={"$toLong": "+"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_minus_only",
        msg="Sign-only string '-' is a conversion failure",
        expression={"$toLong": "-"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_double_minus",
        msg="Double-sign string '--1' is a conversion failure",
        expression={"$toLong": "--1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_comma_separator",
        msg="String with comma separator is a conversion failure",
        expression={"$toLong": "1,000"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_underscore_separator",
        msg="String with underscore separator is a conversion failure",
        expression={"$toLong": "1_000"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_overflow_above_max",
        msg="String exceeding int64 max is a conversion failure",
        expression={"$toLong": "9223372036854775808"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_overflow_below_min",
        msg="String below int64 min is a conversion failure",
        expression={"$toLong": "-9223372036854775809"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_literal_dollar_number",
        msg="'$42' passed via $literal is a conversion failure",
        expression={"$toLong": {"$literal": "$42"}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_literal_dollar_only",
        msg="'$' passed via $literal is a conversion failure",
        expression={"$toLong": {"$literal": "$"}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [String Size Limit]: $toLong checks the byte length of string inputs before
# attempting conversion; strings at or above the limit are rejected unconditionally.
TOLONG_STRING_SIZE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_one_under_valid",
        msg="Valid numeric string one byte under limit converts successfully",
        expression=lazy(lambda: {"$toLong": "0" * (STRING_SIZE_LIMIT_BYTES - 2) + "1"}),
        expected=Int64(1),
    ),
    ExpressionTestCase(
        "size_one_under_non_numeric",
        msg="Non-numeric string one byte under limit passes size check but fails conversion",
        expression=lazy(lambda: {"$toLong": "a" * (STRING_SIZE_LIMIT_BYTES - 1)}),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit",
        msg="String at STRING_SIZE_LIMIT_BYTES is rejected with STRING_SIZE_LIMIT_ERROR",
        expression=lazy(lambda: {"$toLong": "a" * STRING_SIZE_LIMIT_BYTES}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit_four_byte",
        msg="4-byte character string reaching STRING_SIZE_LIMIT_BYTES is rejected",
        expression=lazy(lambda: {"$toLong": "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
]

TOLONG_STRING_TESTS = TOLONG_STRING_NUMERIC_TESTS + TOLONG_STRING_ERROR_TESTS


@pytest.mark.parametrize(
    "test", pytest_params(TOLONG_STRING_TESTS + TOLONG_STRING_SIZE_LIMIT_TESTS)
)
def test_toLong_string(collection, test: ExpressionTestCase):
    """$toLong parses valid integer strings and rejects non-integer or malformed ones."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
