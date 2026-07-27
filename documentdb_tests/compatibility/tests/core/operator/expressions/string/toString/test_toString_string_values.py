"""$toString string passthrough, encoding, and expression argument tests."""

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
from documentdb_tests.framework.parametrize import pytest_params

# Property [String Passthrough]: string input is returned unchanged, preserving whitespace,
# control characters, BSON-meaningful characters, and dollar-prefixed strings via $literal.
TOSTRING_STRING_PASSTHROUGH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_plain",
        msg="Plain string passes through unchanged",
        expression={"$toString": "hello"},
        expected="hello",
    ),
    ExpressionTestCase(
        "string_empty",
        msg="Empty string passes through unchanged",
        expression={"$toString": ""},
        expected="",
    ),
    ExpressionTestCase(
        "string_whitespace",
        msg="Whitespace characters are preserved",
        expression={"$toString": " \t\n\r\u00a0\u2003"},
        expected=" \t\n\r\u00a0\u2003",
    ),
    ExpressionTestCase(
        "string_control_chars",
        msg="Null bytes and control characters are preserved",
        expression={"$toString": "\x00\x01\x1f"},
        expected="\x00\x01\x1f",
    ),
    ExpressionTestCase(
        "string_bson_meaningful_chars",
        msg="BSON-meaningful characters are preserved",
        expression={"$toString": '{}"\\ [],:'},
        expected='{}"\\ [],:',
    ),
    ExpressionTestCase(
        "string_dollar_prefix_literal",
        msg="Dollar-prefixed string via $literal is not treated as a field reference",
        expression={"$toString": {"$literal": "$fieldName"}},
        expected="$fieldName",
    ),
]

# Property [Encoding and Character Handling]: multi-byte UTF-8 characters, Unicode
# normalization forms, zero-width and invisible characters, ZWJ emoji sequences, and
# combining marks are all preserved unchanged through $toString.
TOSTRING_ENCODING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "encoding_2byte_latin",
        msg="2-byte Latin extended character (é) is preserved",
        expression={"$toString": "café"},
        expected="café",
    ),
    ExpressionTestCase(
        "encoding_3byte_cjk",
        msg="3-byte CJK characters are preserved",
        expression={"$toString": "日本語"},
        expected="日本語",
    ),
    ExpressionTestCase(
        "encoding_4byte_emoji",
        msg="4-byte emoji are preserved",
        expression={"$toString": "🚀🎉"},
        expected="🚀🎉",
    ),
    ExpressionTestCase(
        "encoding_4byte_deseret",
        msg="4-byte Deseret character (U+10400) is preserved",
        expression={"$toString": "\U00010400"},
        expected="\U00010400",
    ),
    ExpressionTestCase(
        "encoding_precomposed",
        msg="Precomposed character (U+00E9) is preserved as-is",
        expression={"$toString": "\u00e9"},
        expected="\u00e9",
    ),
    ExpressionTestCase(
        "encoding_decomposed",
        msg="Decomposed character (U+0065 U+0301) is preserved as-is",
        expression={"$toString": "e\u0301"},
        expected="e\u0301",
    ),
    ExpressionTestCase(
        "encoding_bom",
        msg="BOM (U+FEFF) is preserved",
        expression={"$toString": "\ufeff"},
        expected="\ufeff",
    ),
    ExpressionTestCase(
        "encoding_zwsp",
        msg="Zero-width space (U+200B) is preserved",
        expression={"$toString": "\u200b"},
        expected="\u200b",
    ),
    ExpressionTestCase(
        "encoding_zwj",
        msg="Zero-width joiner (U+200D) is preserved",
        expression={"$toString": "\u200d"},
        expected="\u200d",
    ),
    ExpressionTestCase(
        "encoding_directional_marks",
        msg="Directional marks (RTL U+200F, LTR U+200E) are preserved",
        expression={"$toString": "\u200f\u200e"},
        expected="\u200f\u200e",
    ),
    ExpressionTestCase(
        "encoding_zwj_emoji_sequence",
        msg="ZWJ emoji sequence (👨‍💻) is preserved",
        expression={"$toString": "👨\u200d💻"},
        expected="👨\u200d💻",
    ),
    ExpressionTestCase(
        "encoding_combining_mark",
        msg="Combining tilde (U+0303) on 'n' is preserved",
        expression={"$toString": "n\u0303"},
        expected="n\u0303",
    ),
]

# Property [Expression Arguments]: $toString accepts any expression that resolves to a
# convertible type and converts the result.
TOSTRING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expr_int_result",
        msg="$toString converts the result of an integer expression",
        expression={"$toString": {"$add": [10, 20]}},
        expected="30",
    ),
    ExpressionTestCase(
        "expr_string_result",
        msg="$toString passes through the result of a string expression",
        expression={"$toString": {"$concat": ["hello", " ", "world"]}},
        expected="hello world",
    ),
]

TOSTRING_STRING_VALUES_TESTS = with_convert_variants(
    TOSTRING_STRING_PASSTHROUGH_TESTS + TOSTRING_ENCODING_TESTS + TOSTRING_EXPR_TESTS,
    "$toString",
    "string",
)


@pytest.mark.parametrize("test", pytest_params(TOSTRING_STRING_VALUES_TESTS))
def test_toString_string_values(collection, test: ExpressionTestCase):
    """$toString passes strings through unchanged and converts expression results."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
