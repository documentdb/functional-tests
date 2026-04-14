from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [Encoding and Character Handling]: matching is diacritic-sensitive,
# no Unicode normalization is performed, multi-byte UTF-8 characters are
# handled correctly, and special/regex characters are treated literally.
REPLACEONE_ENCODING_TESTS: list[ReplaceOneTest] = [
    # Diacritic sensitivity.
    ReplaceOneTest(
        "encoding_diacritic_no_match",
        input="café",
        find="cafe",
        replacement="X",
        expected="café",
        msg="$replaceOne should handle diacritic no match",
    ),
    ReplaceOneTest(
        "encoding_diaeresis_no_match",
        input="naïve",
        find="naive",
        replacement="X",
        expected="naïve",
        msg="$replaceOne should handle diaeresis no match",
    ),
    ReplaceOneTest(
        "encoding_diacritic_match_first",
        input="résumé",
        find="é",
        replacement="e",
        expected="resumé",
        msg="$replaceOne should handle diacritic match first",
    ),
    # Precomposed U+00E9 does not match decomposed U+0065 U+0301.
    ReplaceOneTest(
        "encoding_precomposed_vs_decomposed",
        input="\u00e9",
        find="e\u0301",
        replacement="X",
        expected="\u00e9",
        msg="$replaceOne should handle precomposed vs decomposed",
    ),
    ReplaceOneTest(
        "encoding_decomposed_vs_precomposed",
        input="e\u0301",
        find="\u00e9",
        replacement="X",
        expected="e\u0301",
        msg="$replaceOne should handle decomposed vs precomposed",
    ),
    # Same representation matches.
    ReplaceOneTest(
        "encoding_precomposed_matches_precomposed",
        input="\u00e9",
        find="\u00e9",
        replacement="X",
        expected="X",
        msg="$replaceOne should handle precomposed matches precomposed",
    ),
    ReplaceOneTest(
        "encoding_decomposed_matches_decomposed",
        input="e\u0301",
        find="e\u0301",
        replacement="X",
        expected="X",
        msg="$replaceOne should handle decomposed matches decomposed",
    ),
    # A base character can be matched independently of a following combining mark.
    ReplaceOneTest(
        "encoding_base_char_splits_combining_mark",
        input="e\u0301",
        find="e",
        replacement="X",
        expected="X\u0301",
        msg="$replaceOne should handle base char splits combining mark",
    ),
    # Multi-byte UTF-8: 2-byte (U+00E9), 3-byte (U+4E16), 4-byte (U+1F600).
    ReplaceOneTest(
        "encoding_2byte_find",
        input="café",
        find="é",
        replacement="e",
        expected="cafe",
        msg="$replaceOne should handle 2byte find",
    ),
    ReplaceOneTest(
        "encoding_3byte_find",
        input="hello世界",
        find="世",
        replacement="X",
        expected="helloX界",
        msg="$replaceOne should handle 3byte find",
    ),
    ReplaceOneTest(
        "encoding_4byte_find",
        input="a😀b😀c",
        find="😀",
        replacement="X",
        expected="aXb😀c",
        msg="$replaceOne should handle 4byte find",
    ),
    ReplaceOneTest(
        "encoding_4byte_replacement",
        input="hello",
        find="h",
        replacement="😀",
        expected="😀ello",
        msg="$replaceOne should handle 4byte replacement",
    ),
]

# Property [Unicode and Encoding]: no Unicode normalization is performed,
# combining marks are independently matchable as regular code points, and
# multi-byte UTF-8 characters of all widths work correctly in all parameter
# positions including mixed byte-width strings.
REPLACEONE_UNICODE_TESTS: list[ReplaceOneTest] = [
    # Combining mark alone (U+0301 combining acute accent) is findable.
    ReplaceOneTest(
        "unicode_combining_mark_find",
        input="e\u0301",
        find="\u0301",
        replacement="X",
        expected="eX",
        msg="$replaceOne unicode combining mark find",
    ),
    # Combining mark alone (U+0303 combining tilde) as replacement.
    ReplaceOneTest(
        "unicode_combining_mark_replacement",
        input="nX",
        find="X",
        replacement="\u0303",
        expected="n\u0303",
        msg="$replaceOne unicode combining mark replacement",
    ),
    # Combining mark deleted by empty replacement.
    ReplaceOneTest(
        "unicode_combining_mark_delete",
        input="e\u0301",
        find="\u0301",
        replacement="",
        expected="e",
        msg="$replaceOne unicode combining mark delete",
    ),
    # 2-byte character (U+00E9) in replacement position.
    ReplaceOneTest(
        "unicode_2byte_replacement",
        input="cafe",
        find="e",
        replacement="\u00e9",
        expected="caf\u00e9",
        msg="$replaceOne unicode 2byte replacement",
    ),
    # 3-byte character (U+4E16) in replacement position.
    ReplaceOneTest(
        "unicode_3byte_replacement",
        input="helloX",
        find="X",
        replacement="\u4e16",
        expected="hello\u4e16",
        msg="$replaceOne unicode 3byte replacement",
    ),
    # 4-byte character in all three positions simultaneously.
    ReplaceOneTest(
        "unicode_4byte_all_positions",
        input="a\U0001f600b",
        find="\U0001f600",
        replacement="\U0001f680",
        expected="a\U0001f680b",
        msg="$replaceOne unicode 4byte all positions",
    ),
    # Mixed byte-width string: 1-byte (a), 2-byte (U+00E9), 3-byte (U+4E16),
    # 4-byte (U+1F600). Find 3-byte char.
    ReplaceOneTest(
        "unicode_mixed_find_3byte",
        input="a\u00e9\u4e16\U0001f600",
        find="\u4e16",
        replacement="X",
        expected="a\u00e9X\U0001f600",
        msg="$replaceOne unicode mixed find 3byte",
    ),
    # Mixed byte-width: find 4-byte char.
    ReplaceOneTest(
        "unicode_mixed_find_4byte",
        input="a\u00e9\u4e16\U0001f600",
        find="\U0001f600",
        replacement="Y",
        expected="a\u00e9\u4e16Y",
        msg="$replaceOne unicode mixed find 4byte",
    ),
    # Mixed byte-width: find 2-byte char.
    ReplaceOneTest(
        "unicode_mixed_find_2byte",
        input="a\u00e9\u4e16\U0001f600",
        find="\u00e9",
        replacement="Z",
        expected="aZ\u4e16\U0001f600",
        msg="$replaceOne unicode mixed find 2byte",
    ),
]

REPLACEONE_ENCODING_ALL_TESTS = REPLACEONE_ENCODING_TESTS + REPLACEONE_UNICODE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_ENCODING_ALL_TESTS))
def test_replaceone_encoding_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne encoding and unicode cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
