from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

from .utils.trim_common import (
    TrimTest,
    _expr,
)

# Property [Encoding and Character Handling]: trimming operates on whole Unicode code points,
# not bytes or substrings.
TRIM_ENCODING_TESTS: list[TrimTest] = [
    # 2-byte UTF-8 character (U+00E9, é).
    TrimTest(
        "enc_2byte_trim",
        input="\u00e9hello\u00e9",
        chars="\u00e9",
        expected="hello",
        msg="$trim should trim 2-byte UTF-8 character é (U+00E9) from both ends",
    ),
    # 3-byte UTF-8 character (U+2603, ☃).
    TrimTest(
        "enc_3byte_trim",
        input="\u2603hello\u2603",
        chars="\u2603",
        expected="hello",
        msg="$trim should trim 3-byte UTF-8 character ☃ (U+2603) from both ends",
    ),
    # 4-byte UTF-8 character (U+1F600, 😀).
    TrimTest(
        "enc_4byte_trim",
        input="\U0001f600hello\U0001f600",
        chars="\U0001f600",
        expected="hello",
        msg="$trim should trim 4-byte UTF-8 character 😀 (U+1F600) from both ends",
    ),
    # Mixed multi-byte characters in chars, each treated individually.
    TrimTest(
        "enc_mixed_multibyte",
        input="\u00e9\u2603\U0001f600hello\U0001f600\u2603\u00e9",
        chars="\U0001f600\u00e9\u2603",
        expected="hello",
        msg="$trim should trim mixed multi-byte characters individually from both ends",
    ),
    # Partial bytes do not match. Trimming "é" (U+00E9) should not affect "e" (U+0065).
    TrimTest(
        "enc_partial_no_match",
        input="ehelloe",
        chars="\u00e9",
        expected="ehelloe",
        msg="$trim should not match partial byte sequences (é vs e)",
    ),
    # Regex-special characters treated as literals.
    TrimTest(
        "enc_regex_special",
        input=".*\\hello\\*.",
        chars="\\*.",
        expected="hello",
        msg="$trim should treat regex-special characters as literals",
    ),
    TrimTest(
        "enc_regex_plus",
        input="+++hello+++",
        chars="+",
        expected="hello",
        msg="$trim should treat + as a literal character",
    ),
    TrimTest(
        "enc_regex_question",
        input="???hello???",
        chars="?",
        expected="hello",
        msg="$trim should treat ? as a literal character",
    ),
    TrimTest(
        "enc_regex_brackets",
        input="(([hello(([",
        chars="([",
        expected="hello",
        msg="$trim should treat ( and [ as literal characters",
    ),
    # Trimming decomposed form: "e" in chars matches the base "e" independently of the
    # following combining mark. Both the leading "e" and trailing "e" are trimmed.
    TrimTest(
        "enc_base_char_strips_from_decomposed",
        input="e\u0301helloe",
        chars="e",
        expected="\u0301hello",
        msg="$trim should trim base char independently from decomposed sequence",
    ),
    # Combining mark (U+0301) is a valid code point and can be trimmed independently of its
    # base character.
    TrimTest(
        "enc_combining_mark_trim",
        input="e\u0301helloe\u0301",
        chars="\u0301",
        expected="e\u0301helloe",
        msg="$trim should trim combining mark (U+0301) only where it appears independently",
    ),
    # Precomposed é in input, decomposed chars "e" + combining acute. Each char in chars is
    # individual, so neither "e" nor U+0301 matches U+00E9.
    TrimTest(
        "enc_decomposed_chars_precomposed_input",
        input="\u00e9hello\u00e9",
        chars="e\u0301",
        expected="\u00e9hello\u00e9",
        msg="$trim should not match precomposed é with decomposed chars e+combining accent",
    ),
    # Case sensitivity: uppercase and lowercase are distinct code points.
    TrimTest(
        "enc_case_lower_no_match",
        input="ABChelloABC",
        chars="abc",
        expected="ABChelloABC",
        msg="$trim should not trim uppercase when chars contains lowercase",
    ),
    TrimTest(
        "enc_case_upper_no_match",
        input="abchelloabc",
        chars="ABC",
        expected="abchelloabc",
        msg="$trim should not trim lowercase when chars contains uppercase",
    ),
    TrimTest(
        "enc_case_exact_match",
        input="AbChelloAbC",
        chars="AbC",
        expected="hello",
        msg="$trim should trim when case matches exactly",
    ),
    # Greek case sensitivity.
    TrimTest(
        "enc_case_greek",
        input="\u03c3hello\u03c3",
        chars="\u03a3",
        expected="\u03c3hello\u03c3",
        msg="$trim should not fold Greek lowercase σ to uppercase Σ",
    ),
    # German sharp s (U+00DF) trimmed as single code point.
    TrimTest(
        "enc_sharp_s",
        input="\u00df\u00dfhello\u00df\u00df",
        chars="\u00df",
        expected="hello",
        msg="$trim should trim ß (U+00DF) as a single code point from both ends",
    ),
    # Surrogate-adjacent code points handled correctly.
    TrimTest(
        "enc_surrogate_adj_d7ff",
        input="\ud7ffhello\ud7ff",
        chars="\ud7ff",
        expected="hello",
        msg="$trim should handle surrogate-adjacent code point U+D7FF",
    ),
    TrimTest(
        "enc_surrogate_adj_e000",
        input="\ue000hello\ue000",
        chars="\ue000",
        expected="hello",
        msg="$trim should handle surrogate-adjacent code point U+E000",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_ENCODING_TESTS))
def test_trim_encoding(collection, test_case: TrimTest):
    """Test $trim encoding and character handling."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
