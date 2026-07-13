"""$toDecimal string parsing error tests: invalid formats and size limit rejections."""

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
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

# Property [String Parsing Errors]: invalid string formats produce CONVERSION_FAILURE_ERROR.
TODECIMAL_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_err_empty",
        msg="$toDecimal should reject empty string",
        expression={"$toDecimal": ""},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_non_numeric",
        msg="$toDecimal should reject non-numeric string",
        expression={"$toDecimal": "h"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_bare_plus",
        msg="$toDecimal should reject bare plus sign",
        expression={"$toDecimal": "+"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_bare_minus",
        msg="$toDecimal should reject bare minus sign",
        expression={"$toDecimal": "-"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_bare_dot",
        msg="$toDecimal should reject bare dot",
        expression={"$toDecimal": "."},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_hex",
        msg="$toDecimal should reject hexadecimal string",
        expression={"$toDecimal": "0x4301"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_leading_space",
        msg="$toDecimal should reject string with leading space",
        expression={"$toDecimal": " 1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_trailing_space",
        msg="$toDecimal should reject string with trailing space",
        expression={"$toDecimal": "1 "},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_embedded_space",
        msg="$toDecimal should reject string with embedded space",
        expression={"$toDecimal": "1 2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_tab",
        msg="$toDecimal should reject string with tab",
        expression={"$toDecimal": "\t1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_newline",
        msg="$toDecimal should reject string with newline",
        expression={"$toDecimal": "\n1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_cr",
        msg="$toDecimal should reject string with carriage return",
        expression={"$toDecimal": "\r1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_nbsp",
        msg="$toDecimal should reject string with non-breaking space (U+00A0)",
        expression={"$toDecimal": "\u00a01"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_en_space",
        msg="$toDecimal should reject string with en space (U+2002)",
        expression={"$toDecimal": "\u20021"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_bom",
        msg="$toDecimal should reject string with BOM (U+FEFF)",
        expression={"$toDecimal": "\ufeff1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_zwsp",
        msg="$toDecimal should reject string with zero-width space (U+200B)",
        expression={"$toDecimal": "\u200b1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_zwj",
        msg="$toDecimal should reject string with zero-width joiner (U+200D)",
        expression={"$toDecimal": "\u200d1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_rtl_mark",
        msg="$toDecimal should reject string with right-to-left mark (U+200F)",
        expression={"$toDecimal": "\u200f1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_incomplete_exp",
        msg="$toDecimal should reject incomplete exponent",
        expression={"$toDecimal": "1E"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_incomplete_exp_plus",
        msg="$toDecimal should reject incomplete exponent with plus",
        expression={"$toDecimal": "1E+"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_incomplete_exp_minus",
        msg="$toDecimal should reject incomplete exponent with minus",
        expression={"$toDecimal": "1E-"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_multi_decimal",
        msg="$toDecimal should reject multiple decimal points",
        expression={"$toDecimal": "1.2.3"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_multi_exponent",
        msg="$toDecimal should reject multiple exponents",
        expression={"$toDecimal": "1E2E3"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_underscore",
        msg="$toDecimal should reject underscore digit separators",
        expression={"$toDecimal": "1_000"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_comma",
        msg="$toDecimal should reject comma digit separators",
        expression={"$toDecimal": "1,000"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_null_byte",
        msg="$toDecimal should reject string with null byte",
        expression={"$toDecimal": "\x001"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_non_ascii_digit",
        msg="$toDecimal should reject non-ASCII digit characters (U+0661)",
        expression={"$toDecimal": "\u0661"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_overflow",
        msg="$toDecimal should reject exponent overflow",
        expression={"$toDecimal": "1E+6145"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_err_underflow",
        msg="$toDecimal should reject exponent underflow",
        expression={"$toDecimal": "1E-6177"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_STRING_ERROR_TESTS))
def test_toDecimal_string_errors(collection, test: ExpressionTestCase):
    """$toDecimal rejects malformed and out-of-range string inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [String Size Limit — Errors]: strings at or above the size limit are rejected with
# STRING_SIZE_LIMIT_ERROR; non-numeric strings just under the limit fail with CONVERSION_FAILURE.
TODECIMAL_STRING_SIZE_LIMIT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_one_under_non_numeric",
        msg="Non-numeric string one byte under limit passes size check but fails conversion",
        expression=lazy(lambda: {"$toDecimal": "a" * (STRING_SIZE_LIMIT_BYTES - 1)}),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit",
        msg="String at STRING_SIZE_LIMIT_BYTES is rejected with STRING_SIZE_LIMIT_ERROR",
        expression=lazy(lambda: {"$toDecimal": "0" * STRING_SIZE_LIMIT_BYTES}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit_four_byte",
        msg="4-byte character string reaching STRING_SIZE_LIMIT_BYTES is rejected",
        expression=lazy(lambda: {"$toDecimal": "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_STRING_SIZE_LIMIT_ERROR_TESTS))
def test_toDecimal_string_size_limit(collection, test: ExpressionTestCase):
    """$toDecimal rejects strings at or above the byte size limit."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
