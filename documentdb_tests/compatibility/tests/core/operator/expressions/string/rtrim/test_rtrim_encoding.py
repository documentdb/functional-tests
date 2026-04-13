from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

from .utils.rtrim_common import (
    RtrimTest,
    _expr,
)

# Property [Encoding and Character Handling]: trimming operates on whole Unicode code points,
# not bytes or substrings.
RTRIM_ENCODING_TESTS: list[RtrimTest] = [
    # 2-byte UTF-8 character (U+00E9, é).
    RtrimTest(
        "enc_2byte_trim",
        input="hello\u00e9",
        chars="\u00e9",
        expected="hello",
        msg="$rtrim should trim 2-byte UTF-8 character é (U+00E9)",
    ),
    # 3-byte UTF-8 character (U+2603, ☃).
    RtrimTest(
        "enc_3byte_trim",
        input="hello\u2603",
        chars="\u2603",
        expected="hello",
        msg="$rtrim should trim 3-byte UTF-8 character ☃ (U+2603)",
    ),
    # 4-byte UTF-8 character (U+1F600, 😀).
    RtrimTest(
        "enc_4byte_trim",
        input="hello\U0001f600",
        chars="\U0001f600",
        expected="hello",
        msg="$rtrim should trim 4-byte UTF-8 character 😀 (U+1F600)",
    ),
    # Mixed multi-byte characters in chars, each treated individually.
    RtrimTest(
        "enc_mixed_multibyte",
        input="hello\u00e9\u2603\U0001f600",
        chars="\U0001f600\u00e9\u2603",
        expected="hello",
        msg="$rtrim should trim mixed multi-byte characters individually",
    ),
    # Partial bytes do not match. Trimming "é" (U+00E9) should not affect "e" (U+0065).
    RtrimTest(
        "enc_partial_no_match",
        input="helloe",
        chars="\u00e9",
        expected="helloe",
        msg="$rtrim should not match partial byte sequences (é vs e)",
    ),
    # Regex-special characters treated as literals.
    RtrimTest(
        "enc_regex_special",
        input="hello.*\\",
        chars="\\*.",
        expected="hello",
        msg="$rtrim should treat regex-special characters as literals",
    ),
    RtrimTest(
        "enc_regex_plus",
        input="hello+++",
        chars="+",
        expected="hello",
        msg="$rtrim should treat + as a literal character",
    ),
    RtrimTest(
        "enc_regex_question",
        input="hello???",
        chars="?",
        expected="hello",
        msg="$rtrim should treat ? as a literal character",
    ),
    RtrimTest(
        "enc_regex_brackets",
        input="hello(([",
        chars="([",
        expected="hello",
        msg="$rtrim should treat ( and [ as literal characters",
    ),
    # Trimming decomposed form from the right: combining mark in chars matches the trailing
    # combining mark independently of the preceding base character.
    RtrimTest(
        "enc_combining_mark_strips_from_decomposed",
        input="helloe\u0301",
        chars="\u0301",
        expected="helloe",
        msg="$rtrim should trim combining mark independently from decomposed sequence",
    ),
    # Combining mark (U+0301) is a valid code point and can be trimmed.
    RtrimTest(
        "enc_combining_mark_trim",
        input="hello\u0301",
        chars="\u0301",
        expected="hello",
        msg="$rtrim should trim standalone combining mark (U+0301)",
    ),
    # Precomposed é in input, decomposed chars "e" + combining acute. Each char in chars is
    # individual, so neither "e" nor U+0301 matches U+00E9.
    RtrimTest(
        "enc_decomposed_chars_precomposed_input",
        input="hello\u00e9",
        chars="e\u0301",
        expected="hello\u00e9",
        msg="$rtrim should not match precomposed é with decomposed chars e+combining accent",
    ),
    # Case sensitivity: uppercase and lowercase are distinct code points.
    RtrimTest(
        "enc_case_lower_no_match",
        input="helloABC",
        chars="abc",
        expected="helloABC",
        msg="$rtrim should not trim uppercase when chars contains lowercase",
    ),
    RtrimTest(
        "enc_case_upper_no_match",
        input="helloabc",
        chars="ABC",
        expected="helloabc",
        msg="$rtrim should not trim lowercase when chars contains uppercase",
    ),
    RtrimTest(
        "enc_case_exact_match",
        input="helloAbC",
        chars="AbC",
        expected="hello",
        msg="$rtrim should trim when case matches exactly",
    ),
    # Greek case sensitivity.
    RtrimTest(
        "enc_case_greek",
        input="hello\u03c3",
        chars="\u03a3",
        expected="hello\u03c3",
        msg="$rtrim should not fold Greek lowercase σ to uppercase Σ",
    ),
    # German sharp s (U+00DF) trimmed as single code point.
    RtrimTest(
        "enc_sharp_s",
        input="hello\u00df\u00df",
        chars="\u00df",
        expected="hello",
        msg="$rtrim should trim ß (U+00DF) as a single code point",
    ),
    # Surrogate-adjacent code points handled correctly.
    RtrimTest(
        "enc_surrogate_adj_d7ff",
        input="hello\ud7ff",
        chars="\ud7ff",
        expected="hello",
        msg="$rtrim should handle surrogate-adjacent code point U+D7FF",
    ),
    RtrimTest(
        "enc_surrogate_adj_e000",
        input="hello\ue000",
        chars="\ue000",
        expected="hello",
        msg="$rtrim should handle surrogate-adjacent code point U+E000",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_ENCODING_TESTS))
def test_rtrim_encoding(collection, test_case: RtrimTest):
    """Test $rtrim encoding and character handling."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
