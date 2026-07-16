"""$toObjectId string validation tests: invalid length, non-hex characters, whitespace, and size limit."""  # noqa: E501

import pytest

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
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR, STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

# Property [Invalid String Length]: strings with byte length other than 24 produce an error.
TOOBJECTID_LENGTH_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "length_empty",
        msg="Empty string is rejected",
        expression={"$toObjectId": ""},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "length_1_byte",
        msg="1-byte string is rejected",
        expression={"$toObjectId": "a"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "length_12_bytes",
        msg="12-byte string is rejected",
        expression={"$toObjectId": "a" * 12},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "length_23_bytes",
        msg="23-byte string is rejected",
        expression={"$toObjectId": "a" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "length_25_bytes",
        msg="25-byte string is rejected",
        expression={"$toObjectId": "a" * 25},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "length_24cp_2byte",
        msg="24 codepoints with 2-byte UTF-8 chars are rejected (byte length is 48, not 24)",
        expression={"$toObjectId": "\u00e9" * 24},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "length_24cp_4byte",
        msg="24 codepoints with 4-byte UTF-8 emoji are rejected (byte length is 96, not 24)",
        expression={"$toObjectId": "\U0001f600" * 24},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [Invalid Hex Characters]: a 24-byte string containing non-hex characters is rejected.
# Tests cover ASCII boundary characters around the valid hex ranges [0-9], [A-F], [a-f].
TOOBJECTID_HEX_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "hex_slash_start",
        msg="'/' (before '0' in ASCII) at position 0 is rejected",
        expression={"$toObjectId": "/" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_colon_start",
        msg="':' (after '9' in ASCII) at position 0 is rejected",
        expression={"$toObjectId": ":" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_at_sign_start",
        msg="'@' (before 'A' in ASCII) at position 0 is rejected",
        expression={"$toObjectId": "@" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_upper_g_start",
        msg="'G' (after 'F' in ASCII) at position 0 is rejected",
        expression={"$toObjectId": "G" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_backtick_start",
        msg="'`' (before 'a' in ASCII) at position 0 is rejected",
        expression={"$toObjectId": "`" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_lower_g_start",
        msg="'g' (after 'f' in ASCII) at position 0 is rejected",
        expression={"$toObjectId": "g" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_slash_middle",
        msg="'/' at position 12 is rejected",
        expression={"$toObjectId": "0" * 12 + "/" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_colon_middle",
        msg="':' at position 12 is rejected",
        expression={"$toObjectId": "0" * 12 + ":" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_upper_g_middle",
        msg="'G' at position 12 is rejected",
        expression={"$toObjectId": "0" * 12 + "G" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_lower_g_middle",
        msg="'g' at position 12 is rejected",
        expression={"$toObjectId": "0" * 12 + "g" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_slash_end",
        msg="'/' at position 23 is rejected",
        expression={"$toObjectId": "0" * 23 + "/"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_colon_end",
        msg="':' at position 23 is rejected",
        expression={"$toObjectId": "0" * 23 + ":"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_upper_g_end",
        msg="'G' at position 23 is rejected",
        expression={"$toObjectId": "0" * 23 + "G"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_lower_g_end",
        msg="'g' at position 23 is rejected",
        expression={"$toObjectId": "0" * 23 + "g"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_null_byte_start",
        msg="Null byte (U+0000) at position 0 is rejected",
        expression={"$toObjectId": "\x00" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_null_byte_middle",
        msg="Null byte (U+0000) at position 12 is rejected",
        expression={"$toObjectId": "0" * 12 + "\x00" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_null_byte_end",
        msg="Null byte (U+0000) at position 23 is rejected",
        expression={"$toObjectId": "0" * 23 + "\x00"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_fullwidth_A",
        msg="Fullwidth 'A' (U+FF21, lookalike of 'A') is rejected",
        expression={"$toObjectId": "\uff21" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_fullwidth_a",
        msg="Fullwidth 'a' (U+FF41, lookalike of 'a') is rejected",
        expression={"$toObjectId": "\uff41" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "hex_cyrillic_a",
        msg="Cyrillic 'а' (U+0430, homoglyph of 'a') is rejected",
        expression={"$toObjectId": "\u0430" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [Whitespace]: no whitespace trimming or Unicode normalization is performed on the
# input string; any whitespace or invisible character causes a conversion failure.
TOOBJECTID_WHITESPACE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ws_leading_space",
        msg="Leading ASCII space is not trimmed and causes rejection",
        expression={"$toObjectId": " 507f1f77bcf86cd79943901"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_trailing_space",
        msg="Trailing ASCII space is not trimmed and causes rejection",
        expression={"$toObjectId": "507f1f77bcf86cd79943901 "},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_middle_space",
        msg="Embedded ASCII space causes rejection",
        expression={"$toObjectId": "507f1f77bcf8 cd799439011"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_tab_start",
        msg="Tab (U+0009) at position 0 causes rejection",
        expression={"$toObjectId": "\t" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_tab_middle",
        msg="Tab (U+0009) at position 12 causes rejection",
        expression={"$toObjectId": "0" * 12 + "\t" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_newline_start",
        msg="Newline (U+000A) at position 0 causes rejection",
        expression={"$toObjectId": "\n" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_newline_middle",
        msg="Newline (U+000A) at position 12 causes rejection",
        expression={"$toObjectId": "0" * 12 + "\n" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_bom_start",
        msg="BOM (U+FEFF) at position 0 causes rejection",
        expression={"$toObjectId": "\ufeff" + "0" * 23},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "ws_zwsp_middle",
        msg="Zero-width space (U+200B) at position 12 causes rejection",
        expression={"$toObjectId": "0" * 12 + "\u200b" + "0" * 11},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [String Size Limit]: strings at or above the 16 MB byte limit are rejected with a
# string size limit error before hex validation is attempted.
TOOBJECTID_STRING_SIZE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_one_under",
        msg="Non-hex string one byte under the limit passes the size check but fails conversion",
        expression=lazy(lambda: {"$toObjectId": "a" * (STRING_SIZE_LIMIT_BYTES - 1)}),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit",
        msg="String at STRING_SIZE_LIMIT_BYTES is rejected with STRING_SIZE_LIMIT_ERROR",
        expression=lazy(lambda: {"$toObjectId": "a" * STRING_SIZE_LIMIT_BYTES}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit_four_byte",
        msg="Four-byte character string reaching 16 MB bytes is rejected with STRING_SIZE_LIMIT_ERROR",  # noqa: E501
        expression=lazy(lambda: {"$toObjectId": "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
]

TOOBJECTID_STRING_TESTS = with_convert_variants(
    TOOBJECTID_LENGTH_ERROR_TESTS
    + TOOBJECTID_HEX_ERROR_TESTS
    + TOOBJECTID_WHITESPACE_ERROR_TESTS
    + TOOBJECTID_STRING_SIZE_LIMIT_TESTS,
    "$toObjectId",
    "objectId",
)


@pytest.mark.parametrize("test", pytest_params(TOOBJECTID_STRING_TESTS))
def test_toObjectId_string(collection, test: ExpressionTestCase):
    """$toObjectId rejects invalid strings: wrong length, non-hex chars, whitespace, size limit."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
