from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.substrBytes.utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Encoding]: characters of various byte widths and special byte values are correctly
# extracted when start and length align with byte boundaries.
SUBSTRBYTES_ENCODING_TESTS: list[SubstrBytesTest] = [
    # 2-byte characters (U+03C3 σ).
    SubstrBytesTest(
        "encoding_2byte_sigma",
        string="σ",
        byte_index=0,
        byte_count=2,
        expected="σ",
        msg="$substrBytes should extract 2-byte character",
    ),
    # 3-byte characters (U+4E2D 中).
    SubstrBytesTest(
        "encoding_3byte_zhong",
        string="中",
        byte_index=0,
        byte_count=3,
        expected="中",
        msg="$substrBytes should extract 3-byte character",
    ),
    # 4-byte characters (U+1F600 😀, U+10400 Deseret 𐐀).
    SubstrBytesTest(
        "encoding_4byte_grinning",
        string="😀",
        byte_index=0,
        byte_count=4,
        expected="😀",
        msg="$substrBytes should extract 4-byte emoji",
    ),
    SubstrBytesTest(
        "encoding_4byte_deseret",
        string="\U00010400",
        byte_index=0,
        byte_count=4,
        expected="\U00010400",
        msg="$substrBytes should extract 4-byte Deseret character",
    ),
    # Mixed ASCII and multi-byte: "aé中😀" = 1 + 2 + 3 + 4 = 10 bytes.
    SubstrBytesTest(
        "encoding_mixed_ascii",
        string="aé中😀",
        byte_index=0,
        byte_count=1,
        expected="a",
        msg="$substrBytes should extract ASCII byte from mixed string",
    ),
    SubstrBytesTest(
        "encoding_mixed_2byte",
        string="aé中😀",
        byte_index=1,
        byte_count=2,
        expected="é",
        msg="$substrBytes should extract 2-byte char from mixed string",
    ),
    SubstrBytesTest(
        "encoding_mixed_3byte",
        string="aé中😀",
        byte_index=3,
        byte_count=3,
        expected="中",
        msg="$substrBytes should extract 3-byte char from mixed string",
    ),
    SubstrBytesTest(
        "encoding_mixed_4byte",
        string="aé中😀",
        byte_index=6,
        byte_count=4,
        expected="😀",
        msg="$substrBytes should extract 4-byte char from mixed string",
    ),
    # Extract multiple multi-byte characters in one slice.
    SubstrBytesTest(
        "encoding_mixed_2byte_and_3byte",
        string="aé中😀",
        byte_index=1,
        byte_count=5,
        expected="é中",
        msg="$substrBytes should extract 2-byte and 3-byte chars in one slice",
    ),
    SubstrBytesTest(
        "encoding_mixed_3byte_and_4byte",
        string="aé中😀",
        byte_index=3,
        byte_count=7,
        expected="中😀",
        msg="$substrBytes should extract 3-byte and 4-byte chars in one slice",
    ),
    SubstrBytesTest(
        "encoding_mixed_full",
        string="aé中😀",
        byte_index=0,
        byte_count=10,
        expected="aé中😀",
        msg="$substrBytes should extract full mixed multi-byte string",
    ),
    # Precomposed é (U+00E9) is 2 bytes.
    SubstrBytesTest(
        "encoding_precomposed_e_accent",
        string="\u00e9",
        byte_index=0,
        byte_count=2,
        expected="\u00e9",
        msg="$substrBytes should extract precomposed 2-byte character",
    ),
    # Decomposed e + combining acute (U+0301) is 3 bytes total.
    SubstrBytesTest(
        "encoding_decomposed_e_accent",
        string="e\u0301",
        byte_index=0,
        byte_count=3,
        expected="e\u0301",
        msg="$substrBytes should extract decomposed 3-byte sequence",
    ),
    # Null bytes are preserved and do not terminate the string.
    SubstrBytesTest(
        "encoding_null_byte_full",
        string="a\x00b",
        byte_index=0,
        byte_count=3,
        expected="a\x00b",
        msg="$substrBytes should preserve null bytes",
    ),
    SubstrBytesTest(
        "encoding_null_byte_after",
        string="a\x00b",
        byte_index=2,
        byte_count=1,
        expected="b",
        msg="$substrBytes should extract byte after null byte",
    ),
    SubstrBytesTest(
        "encoding_null_byte_extract",
        string="a\x00b",
        byte_index=1,
        byte_count=1,
        expected="\x00",
        msg="$substrBytes should extract null byte itself",
    ),
    # Control characters are preserved.
    SubstrBytesTest(
        "encoding_control_chars",
        string="\x01\x02\x1f",
        byte_index=0,
        byte_count=3,
        expected="\x01\x02\x1f",
        msg="$substrBytes should preserve control characters",
    ),
    SubstrBytesTest(
        "encoding_control_char_mid",
        string="\x01\x02\x1f",
        byte_index=1,
        byte_count=1,
        expected="\x02",
        msg="$substrBytes should extract control character from middle",
    ),
    # Whitespace characters are preserved and extractable.
    SubstrBytesTest(
        "encoding_whitespace",
        string=" \t\n\r",
        byte_index=0,
        byte_count=4,
        expected=" \t\n\r",
        msg="$substrBytes should preserve whitespace characters",
    ),
    SubstrBytesTest(
        "encoding_newline",
        string=" \t\n\r",
        byte_index=2,
        byte_count=1,
        expected="\n",
        msg="$substrBytes should extract newline character",
    ),
    # Unicode whitespace: NBSP U+00A0 (2 bytes), en space U+2000 (3 bytes).
    SubstrBytesTest(
        "encoding_nbsp",
        string="\u00a0",
        byte_index=0,
        byte_count=2,
        expected="\u00a0",
        msg="$substrBytes should extract 2-byte NBSP",
    ),
    SubstrBytesTest(
        "encoding_en_space",
        string="\u2000",
        byte_index=0,
        byte_count=3,
        expected="\u2000",
        msg="$substrBytes should extract 3-byte en space",
    ),
    # Zero-width characters: ZWSP U+200B (3 bytes), ZWJ U+200D (3 bytes).
    SubstrBytesTest(
        "encoding_zwsp",
        string="\u200b",
        byte_index=0,
        byte_count=3,
        expected="\u200b",
        msg="$substrBytes should extract 3-byte zero-width space",
    ),
    SubstrBytesTest(
        "encoding_zwj",
        string="\u200d",
        byte_index=0,
        byte_count=3,
        expected="\u200d",
        msg="$substrBytes should extract 3-byte zero-width joiner",
    ),
    # BOM U+FEFF is preserved and occupies 3 bytes.
    SubstrBytesTest(
        "encoding_bom",
        string="\ufeff",
        byte_index=0,
        byte_count=3,
        expected="\ufeff",
        msg="$substrBytes should extract 3-byte BOM",
    ),
    # BSON/JSON-significant characters are treated as data.
    SubstrBytesTest(
        "encoding_bson_json_chars",
        string='{}"$\\[]',
        byte_index=0,
        byte_count=7,
        expected='{}"$\\[]',
        msg="$substrBytes should treat BSON/JSON characters as data",
    ),
    SubstrBytesTest(
        "encoding_bson_json_dollar",
        string='{}"$\\[]',
        byte_index=3,
        byte_count=1,
        expected="$",
        msg="$substrBytes should extract dollar sign from BSON/JSON string",
    ),
    # $literal prevents $-prefixed strings from being misinterpreted as field references.
    SubstrBytesTest(
        "encoding_literal_dollar_prefix",
        string={"$literal": "$field"},
        byte_index=0,
        byte_count=6,
        expected="$field",
        msg="$substrBytes should handle $literal dollar-prefixed string",
    ),
]

# Property [Grapheme Splitting]: the operator splits at byte boundaries, not grapheme cluster
# boundaries, so combining marks and ZWJ emoji components are extracted independently.
SUBSTRBYTES_GRAPHEME_SPLIT_TESTS: list[SubstrBytesTest] = [
    # Base character extracted independently of following combining mark.
    SubstrBytesTest(
        "grapheme_base_without_combining",
        string="e\u0301",
        byte_index=0,
        byte_count=1,
        expected="e",
        msg="$substrBytes should extract base character without combining mark",
    ),
    # Combining mark extracted alone.
    SubstrBytesTest(
        "grapheme_combining_mark_alone",
        string="e\u0301",
        byte_index=1,
        byte_count=2,
        expected="\u0301",
        msg="$substrBytes should extract combining mark alone",
    ),
    # ZWJ emoji sequence: 👨 (4 bytes) + ZWJ U+200D (3 bytes) + 👩 (4 bytes) = 11 bytes.
    SubstrBytesTest(
        "grapheme_zwj_emoji_first",
        string="👨\u200d👩",
        byte_index=0,
        byte_count=4,
        expected="👨",
        msg="$substrBytes should extract first emoji from ZWJ sequence",
    ),
    SubstrBytesTest(
        "grapheme_zwj_emoji_joiner",
        string="👨\u200d👩",
        byte_index=4,
        byte_count=3,
        expected="\u200d",
        msg="$substrBytes should extract ZWJ joiner from emoji sequence",
    ),
    SubstrBytesTest(
        "grapheme_zwj_emoji_second",
        string="👨\u200d👩",
        byte_index=7,
        byte_count=4,
        expected="👩",
        msg="$substrBytes should extract second emoji from ZWJ sequence",
    ),
]


SUBSTRBYTES_ENCODING_ALL_TESTS = SUBSTRBYTES_ENCODING_TESTS + SUBSTRBYTES_GRAPHEME_SPLIT_TESTS


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_ENCODING_ALL_TESTS))
def test_substrbytes_encoding(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
