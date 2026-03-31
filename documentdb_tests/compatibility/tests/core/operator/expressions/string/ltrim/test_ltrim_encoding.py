from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.ltrim.utils.ltrim_common import (
    LtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Encoding and Character Handling]: trimming operates on whole Unicode code points,
# not bytes or substrings.
LTRIM_ENCODING_TESTS: list[LtrimTest] = [
    # 2-byte UTF-8 character (U+00E9, é).
    LtrimTest(
        "enc_2byte_trim",
        input="\u00e9hello",
        chars="\u00e9",
        expected="hello",
        msg="$ltrim should trim 2-byte UTF-8 character é (U+00E9)",
    ),
    # 3-byte UTF-8 character (U+2603, ☃).
    LtrimTest(
        "enc_3byte_trim",
        input="\u2603hello",
        chars="\u2603",
        expected="hello",
        msg="$ltrim should trim 3-byte UTF-8 character ☃ (U+2603)",
    ),
    # 4-byte UTF-8 character (U+1F600, 😀).
    LtrimTest(
        "enc_4byte_trim",
        input="\U0001f600hello",
        chars="\U0001f600",
        expected="hello",
        msg="$ltrim should trim 4-byte UTF-8 character 😀 (U+1F600)",
    ),
    # Mixed multi-byte characters in chars, each treated individually.
    LtrimTest(
        "enc_mixed_multibyte",
        input="\u00e9\u2603\U0001f600hello",
        chars="\U0001f600\u00e9\u2603",
        expected="hello",
        msg="$ltrim should trim mixed multi-byte characters individually",
    ),
    # Partial bytes do not match. Trimming "é" (U+00E9) should not affect "e" (U+0065).
    LtrimTest(
        "enc_partial_no_match",
        input="ehello",
        chars="\u00e9",
        expected="ehello",
        msg="$ltrim should not match partial byte sequences (é vs e)",
    ),
    # Regex-special characters treated as literals.
    LtrimTest(
        "enc_regex_special",
        input=".*\\hello",
        chars="\\*.",
        expected="hello",
        msg="$ltrim should treat regex-special characters as literals",
    ),
    LtrimTest(
        "enc_regex_plus",
        input="+++hello",
        chars="+",
        expected="hello",
        msg="$ltrim should treat + as a literal character",
    ),
    LtrimTest(
        "enc_regex_question",
        input="???hello",
        chars="?",
        expected="hello",
        msg="$ltrim should treat ? as a literal character",
    ),
    LtrimTest(
        "enc_regex_brackets",
        input="(([hello",
        chars="([",
        expected="hello",
        msg="$ltrim should treat ( and [ as literal characters",
    ),
    # Trimming decomposed form: "e" in chars matches the base "e" independently of the
    # following combining mark.
    LtrimTest(
        "enc_base_char_strips_from_decomposed",
        input="e\u0301hello",
        chars="e",
        expected="\u0301hello",
        msg="$ltrim should trim base char independently from decomposed sequence",
    ),
    # Combining mark (U+0301) is a valid code point and can be trimmed.
    LtrimTest(
        "enc_combining_mark_trim",
        input="\u0301hello",
        chars="\u0301",
        expected="hello",
        msg="$ltrim should trim standalone combining mark (U+0301)",
    ),
    # Precomposed é in input, decomposed chars "e" + combining acute. Each char in chars is
    # individual, so neither "e" nor U+0301 matches U+00E9.
    LtrimTest(
        "enc_decomposed_chars_precomposed_input",
        input="\u00e9hello",
        chars="e\u0301",
        expected="\u00e9hello",
        msg="$ltrim should not match precomposed é with decomposed chars e+combining accent",
    ),
    # Case sensitivity: uppercase and lowercase are distinct code points.
    LtrimTest(
        "enc_case_lower_no_match",
        input="ABChello",
        chars="abc",
        expected="ABChello",
        msg="$ltrim should not trim uppercase when chars contains lowercase",
    ),
    LtrimTest(
        "enc_case_upper_no_match",
        input="abchello",
        chars="ABC",
        expected="abchello",
        msg="$ltrim should not trim lowercase when chars contains uppercase",
    ),
    LtrimTest(
        "enc_case_exact_match",
        input="AbChello",
        chars="AbC",
        expected="hello",
        msg="$ltrim should trim when case matches exactly",
    ),
    # Greek case sensitivity.
    LtrimTest(
        "enc_case_greek",
        input="\u03c3hello",
        chars="\u03a3",
        expected="\u03c3hello",
        msg="$ltrim should not fold Greek lowercase σ to uppercase Σ",
    ),
    # German sharp s (U+00DF) trimmed as single code point.
    LtrimTest(
        "enc_sharp_s",
        input="\u00df\u00dfhello",
        chars="\u00df",
        expected="hello",
        msg="$ltrim should trim ß (U+00DF) as a single code point",
    ),
    # Surrogate-adjacent code points handled correctly.
    LtrimTest(
        "enc_surrogate_adj_d7ff",
        input="\ud7ffhello",
        chars="\ud7ff",
        expected="hello",
        msg="$ltrim should handle surrogate-adjacent code point U+D7FF",
    ),
    LtrimTest(
        "enc_surrogate_adj_e000",
        input="\ue000hello",
        chars="\ue000",
        expected="hello",
        msg="$ltrim should handle surrogate-adjacent code point U+E000",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_ENCODING_TESTS))
def test_ltrim_encoding(collection, test_case: LtrimTest):
    """Test $ltrim encoding and character handling cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
