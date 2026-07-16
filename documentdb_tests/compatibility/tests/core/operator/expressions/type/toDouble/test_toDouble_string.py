"""$toDouble string conversion tests: valid numeric, scientific notation, hex float, and errors."""

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
    DOUBLE_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [String Numeric]: $toDouble parses decimal, scientific-notation, and infinity strings.
TODOUBLE_STRING_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_zero", msg="'0' converts to 0.0", expression={"$toDouble": "0"}, expected=DOUBLE_ZERO
    ),
    ExpressionTestCase(
        "str_one", msg="'1' converts to 1.0", expression={"$toDouble": "1"}, expected=1.0
    ),
    ExpressionTestCase(
        "str_neg_one", msg="'-1' converts to -1.0", expression={"$toDouble": "-1"}, expected=-1.0
    ),
    ExpressionTestCase(
        "str_plus_one", msg="'+1' converts to 1.0", expression={"$toDouble": "+1"}, expected=1.0
    ),
    ExpressionTestCase(
        "str_decimal",
        msg="'1.5' converts to 1.5",
        expression={"$toDouble": "1.5"},
        expected=DOUBLE_ONE_AND_HALF,
    ),
    ExpressionTestCase(
        "str_dot_five",
        msg="'.5' converts to 0.5",
        expression={"$toDouble": ".5"},
        expected=DOUBLE_HALF,
    ),
    ExpressionTestCase(
        "str_neg_zero",
        msg="'-0' converts to -0.0",
        expression={"$toDouble": "-0"},
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "str_sci_pos",
        msg="'1e10' (scientific) converts correctly",
        expression={"$toDouble": "1e10"},
        expected=1e10,
    ),
    ExpressionTestCase(
        "str_sci_neg_exp",
        msg="'1.5e-3' (scientific negative exponent) converts correctly",
        expression={"$toDouble": "1.5e-3"},
        expected=1.5e-3,
    ),
    ExpressionTestCase(
        "str_sci_upper",
        msg="'1E10' (uppercase E) converts correctly",
        expression={"$toDouble": "1E10"},
        expected=1e10,
    ),
    ExpressionTestCase(
        "str_inf",
        msg="'Infinity' converts to +Inf",
        expression={"$toDouble": "Infinity"},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "str_neg_inf",
        msg="'-Infinity' converts to -Inf",
        expression={"$toDouble": "-Infinity"},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "str_plus_inf",
        msg="'+Infinity' converts to +Inf",
        expression={"$toDouble": "+Infinity"},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "str_inf_short",
        msg="'inf' converts to +Inf",
        expression={"$toDouble": "inf"},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "str_neg_inf_short",
        msg="'-inf' converts to -Inf",
        expression={"$toDouble": "-inf"},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
]

# Property [String Hex]: $toDouble parses hexadecimal float literals (requires a leading sign for
# lowercase inputs).
TODOUBLE_STRING_HEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_hex_zero",
        msg="'+0x0p0' converts to 0.0",
        expression={"$toDouble": "+0x0p0"},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "str_hex_one",
        msg="'+0x1p0' converts to 1.0",
        expression={"$toDouble": "+0x1p0"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_two",
        msg="'+0x1p1' converts to 2.0",
        expression={"$toDouble": "+0x1p1"},
        expected=2.0,
    ),
    ExpressionTestCase(
        "str_hex_half",
        msg="'+0x1p-1' converts to 0.5",
        expression={"$toDouble": "+0x1p-1"},
        expected=DOUBLE_HALF,
    ),
    ExpressionTestCase(
        "str_hex_frac",
        msg="'+0x1.8p1' converts to 3.0",
        expression={"$toDouble": "+0x1.8p1"},
        expected=3.0,
    ),
    ExpressionTestCase(
        "str_hex_neg",
        msg="'-0x1p0' converts to -1.0",
        expression={"$toDouble": "-0x1p0"},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "str_hex_plus",
        msg="'+0x1p0' converts to 1.0",
        expression={"$toDouble": "+0x1p0"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_upper",
        msg="'0X1P0' (uppercase) converts to 1.0",
        expression={"$toDouble": "0X1P0"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_ff",
        msg="'+0xffp0' converts to 255.0",
        expression={"$toDouble": "+0xffp0"},
        expected=255.0,
    ),
    ExpressionTestCase(
        "str_hex_bare_int",
        msg="'+0x1' (bare hex integer) converts to 1.0",
        expression={"$toDouble": "+0x1"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_bare_ff",
        msg="'+0xff' (bare hex integer) converts to 255.0",
        expression={"$toDouble": "+0xff"},
        expected=255.0,
    ),
    ExpressionTestCase(
        "str_hex_err_no_digits",
        msg="'0x' (prefix only) is a conversion failure",
        expression={"$toDouble": "0x"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_hex_err_p_no_exp",
        msg="'0x1p' (missing exponent digits) is a conversion failure",
        expression={"$toDouble": "0x1p"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_hex_err_no_sig",
        msg="'0xp0' (missing significand digits) is a conversion failure",
        expression={"$toDouble": "0xp0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_hex_err_dot_only",
        msg="'0x.p0' (dot but no digits) is a conversion failure",
        expression={"$toDouble": "0x.p0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [String Errors]: $toDouble rejects malformed, whitespace-padded, and out-of-range
# strings with a conversion failure.
TODOUBLE_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_alpha",
        msg="Alphabetic string is a conversion failure",
        expression={"$toDouble": "abc"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_empty",
        msg="Empty string is a conversion failure",
        expression={"$toDouble": ""},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_leading_space",
        msg="Leading whitespace is a conversion failure",
        expression={"$toDouble": " 1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_trailing_space",
        msg="Trailing whitespace is a conversion failure",
        expression={"$toDouble": "1 "},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_embedded_space",
        msg="Embedded whitespace is a conversion failure",
        expression={"$toDouble": "1 2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_overflow",
        msg="Overflow string (> double max) is a conversion failure",
        expression={"$toDouble": "1e309"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_underflow",
        msg="Underflow string (< double min subnormal) is a conversion failure",
        expression={"$toDouble": "1e-400"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_partial_sci",
        msg="Incomplete scientific notation is a conversion failure",
        expression={"$toDouble": "1.5e"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TODOUBLE_STRING_TESTS = (
    TODOUBLE_STRING_NUMERIC_TESTS + TODOUBLE_STRING_HEX_TESTS + TODOUBLE_STRING_ERROR_TESTS
)


# Property [String Size Limit]: $toDouble checks the byte length of string inputs before
# attempting conversion; strings at or above the limit are rejected unconditionally.
TODOUBLE_STRING_SIZE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_one_under_valid",
        msg="Valid numeric string one byte under limit converts successfully",
        expression=lazy(lambda: {"$toDouble": "0" * (STRING_SIZE_LIMIT_BYTES - 2) + "1"}),
        expected=1.0,
    ),
    ExpressionTestCase(
        "size_one_under_hex",
        msg="Valid hex string one byte under limit converts successfully",
        expression=lazy(lambda: {"$toDouble": "0X" + "0" * (STRING_SIZE_LIMIT_BYTES - 4) + "F"}),
        expected=15.0,
    ),
    ExpressionTestCase(
        "size_one_under_non_numeric",
        msg="Non-numeric string one byte under limit passes size check but fails conversion",
        expression=lazy(lambda: {"$toDouble": "a" * (STRING_SIZE_LIMIT_BYTES - 1)}),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit",
        msg="String at STRING_SIZE_LIMIT_BYTES is rejected with STRING_SIZE_LIMIT_ERROR",
        expression=lazy(lambda: {"$toDouble": "a" * STRING_SIZE_LIMIT_BYTES}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit_four_byte",
        msg="4-byte character string reaching STRING_SIZE_LIMIT_BYTES is rejected",
        expression=lazy(lambda: {"$toDouble": "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TODOUBLE_STRING_TESTS + TODOUBLE_STRING_SIZE_LIMIT_TESTS)
)
def test_toDouble_string(collection, test: ExpressionTestCase):
    """$toDouble parses valid numeric strings and rejects malformed ones."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
