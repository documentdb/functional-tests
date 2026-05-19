from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.split_common import (
    SplitTest,
    _expr,
)

# Property [Encoding and Character Handling]: the delimiter is matched as a
# literal string, with correct handling of multi-byte UTF-8, special
# characters, and no Unicode normalization.
SPLIT_ENCODING_TESTS: list[SplitTest] = [
    # Regex special characters treated as literals.
    SplitTest(
        "encoding_dot_delim",
        string="a.b.c",
        delimiter=".",
        expected=["a", "b", "c"],
        msg="$split should treat dot as literal, not regex wildcard",
    ),
    SplitTest(
        "encoding_star_delim",
        string="a*b*c",
        delimiter="*",
        expected=["a", "b", "c"],
        msg="$split should treat star as literal, not regex quantifier",
    ),
    SplitTest(
        "encoding_backslash_delim",
        string="a\\b\\c",
        delimiter="\\",
        expected=["a", "b", "c"],
        msg="$split should treat backslash as literal delimiter",
    ),
    # JSON/BSON-meaningful characters work as content and delimiters.
    SplitTest(
        "encoding_brace_delim",
        string="a{b}c",
        delimiter="{",
        expected=["a", "b}c"],
        msg="$split should treat brace as literal delimiter",
    ),
    SplitTest(
        "encoding_pipe_delim",
        string="a|b|c",
        delimiter="|",
        expected=["a", "b", "c"],
        msg="$split should treat pipe as literal delimiter",
    ),
    # 2-byte UTF-8 (e.g., U+00E9 é).
    SplitTest(
        "encoding_2byte_in_string",
        string="café-résumé",
        delimiter="-",
        expected=["café", "résumé"],
        msg="$split should correctly split strings containing 2-byte UTF-8 characters",
    ),
    SplitTest(
        "encoding_2byte_as_delim",
        string="caférésumééblanc",
        delimiter="\u00e9",
        expected=["caf", "r", "sum", "", "blanc"],
        msg="$split should use 2-byte UTF-8 character as delimiter",
    ),
    # 3-byte UTF-8 (e.g., U+263A ☺).
    SplitTest(
        "encoding_3byte_as_delim",
        string="a\u263ab\u263ac",
        delimiter="\u263a",
        expected=["a", "b", "c"],
        msg="$split should use 3-byte UTF-8 character as delimiter",
    ),
    # 4-byte UTF-8 (e.g., U+1F389 🎉).
    SplitTest(
        "encoding_4byte_as_delim",
        string="a\U0001f389b\U0001f389c",
        delimiter="\U0001f389",
        expected=["a", "b", "c"],
        msg="$split should use 4-byte UTF-8 character as delimiter",
    ),
    # Special characters as delimiters.
    SplitTest(
        "encoding_newline_delim",
        string="hello\nworld\nfoo",
        delimiter="\n",
        expected=["hello", "world", "foo"],
        msg="$split should split on newline delimiter",
    ),
    SplitTest(
        "encoding_tab_delim",
        string="hello\tworld",
        delimiter="\t",
        expected=["hello", "world"],
        msg="$split should split on tab delimiter",
    ),
    SplitTest(
        "encoding_null_byte_delim",
        string="hello\x00world",
        delimiter="\x00",
        expected=["hello", "world"],
        msg="$split should split on null byte delimiter",
    ),
    # Multi-char special delimiter.
    SplitTest(
        "encoding_crlf_delim",
        string="hello\r\nworld\r\nfoo",
        delimiter="\r\n",
        expected=["hello", "world", "foo"],
        msg="$split should split on CRLF as a two-character delimiter",
    ),
    # Precomposed U+00E9 and decomposed U+0065+U+0301 are distinct.
    SplitTest(
        "encoding_precomposed_not_matched_by_decomposed",
        string="caf\u00e9",
        delimiter="\u0065\u0301",
        expected=["caf\u00e9"],
        msg="$split should not match precomposed character with decomposed delimiter",
    ),
    SplitTest(
        "encoding_decomposed_not_matched_by_precomposed",
        string="caf\u0065\u0301",
        delimiter="\u00e9",
        expected=["caf\u0065\u0301"],
        msg="$split should not match decomposed character with precomposed delimiter",
    ),
    # Base character matches independently of following combining mark.
    SplitTest(
        "encoding_base_char_splits_before_combining_mark",
        string="caf\u0065\u0301",
        delimiter="e",
        expected=["caf", "\u0301"],
        msg="$split should split on base character leaving combining mark in next segment",
    ),
    # ZWJ (U+200D) is treated as a regular code point.
    SplitTest(
        "encoding_zwj_splits_emoji_sequence",
        string="\U0001f468\u200d\U0001f469\u200d\U0001f467",
        delimiter="\u200d",
        expected=["\U0001f468", "\U0001f469", "\U0001f467"],
        msg="$split should split ZWJ emoji sequence on ZWJ character",
    ),
    # BOM (U+FEFF) as delimiter.
    SplitTest(
        "encoding_bom_delim",
        string="a\ufeffb\ufeffc",
        delimiter="\ufeff",
        expected=["a", "b", "c"],
        msg="$split should split on BOM character as delimiter",
    ),
    # Zero-width space (U+200B) as delimiter.
    SplitTest(
        "encoding_zero_width_space_delim",
        string="a\u200bb\u200bc",
        delimiter="\u200b",
        expected=["a", "b", "c"],
        msg="$split should split on zero-width space as delimiter",
    ),
    # Directional marks as delimiters: LRM (U+200E) and RLM (U+200F).
    SplitTest(
        "encoding_lrm_delim",
        string="a\u200eb\u200ec",
        delimiter="\u200e",
        expected=["a", "b", "c"],
        msg="$split should split on left-to-right mark as delimiter",
    ),
    SplitTest(
        "encoding_rlm_delim",
        string="a\u200fb\u200fc",
        delimiter="\u200f",
        expected=["a", "b", "c"],
        msg="$split should split on right-to-left mark as delimiter",
    ),
    # Control character (U+0001) as delimiter.
    SplitTest(
        "encoding_control_char_delim",
        string="a\x01b\x01c",
        delimiter="\x01",
        expected=["a", "b", "c"],
        msg="$split should split on control character as delimiter",
    ),
    # Different whitespace characters do not match each other.
    SplitTest(
        "encoding_tab_not_space",
        string="a\tb",
        delimiter=" ",
        expected=["a\tb"],
        msg="$split should not match tab when delimiter is space",
    ),
    # NBSP (U+00A0) does not match ASCII space.
    SplitTest(
        "encoding_nbsp_not_space",
        string="a\u00a0b",
        delimiter=" ",
        expected=["a\u00a0b"],
        msg="$split should not match non-breaking space when delimiter is ASCII space",
    ),
    # Splitting CRLF by \n leaves \r attached to preceding segment.
    SplitTest(
        "encoding_crlf_split_by_lf",
        string="hello\r\nworld",
        delimiter="\n",
        expected=["hello\r", "world"],
        msg="$split on LF should leave CR attached to preceding segment",
    ),
    # Splitting CRLF by \r leaves \n attached to following segment.
    SplitTest(
        "encoding_crlf_split_by_cr",
        string="hello\r\nworld",
        delimiter="\r",
        expected=["hello", "\nworld"],
        msg="$split on CR should leave LF attached to following segment",
    ),
    # Escape sequence \d as delimiter does not match digits (literal matching).
    SplitTest(
        "encoding_backslash_d_literal",
        string="a1b2c",
        delimiter="\\d",
        expected=["a1b2c"],
        msg="$split should treat backslash-d as literal two-char string, not regex digit class",
    ),
]

# Property [Case Sensitivity]: splitting is always case-sensitive for all
# scripts.
SPLIT_CASE_SENSITIVITY_TESTS: list[SplitTest] = [
    # ASCII: uppercase "H" does not match lowercase "h".
    SplitTest(
        "case_ascii",
        string="Hello-hello-HELLO",
        delimiter="hello",
        expected=["Hello-", "-HELLO"],
        msg="$split should be case-sensitive for ASCII letters",
    ),
    # Latin extended: U+00E9 (é) does not match U+00C9 (É).
    SplitTest(
        "case_latin_extended",
        string="café-cafÉ",
        delimiter="\u00e9",
        expected=["caf", "-cafÉ"],
        msg="$split should be case-sensitive for Latin extended characters",
    ),
    # Greek: U+03C3 (σ) does not match U+03A3 (Σ).
    SplitTest(
        "case_greek",
        string="\u03c3-\u03a3-\u03c3",
        delimiter="\u03a3",
        expected=["\u03c3-", "-\u03c3"],
        msg="$split should be case-sensitive for Greek letters",
    ),
    # Cyrillic: U+0430 (а) does not match U+0410 (А).
    SplitTest(
        "case_cyrillic",
        string="\u0430-\u0410-\u0430",
        delimiter="\u0410",
        expected=["\u0430-", "-\u0430"],
        msg="$split should be case-sensitive for Cyrillic letters",
    ),
]

SPLIT_ENCODING_ALL_TESTS = SPLIT_ENCODING_TESTS + SPLIT_CASE_SENSITIVITY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_ENCODING_ALL_TESTS))
def test_split_encoding_cases(collection, test_case: SplitTest):
    """Test $split encoding, character handling, and case sensitivity cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
