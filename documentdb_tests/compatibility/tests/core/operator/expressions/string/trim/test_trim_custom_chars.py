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

# Property [Custom Chars]: when chars is provided, only those characters are trimmed from both
# ends. Each character in chars is treated individually (not as a substring), and the order of
# characters in chars does not affect the result.
TRIM_CUSTOM_CHARS_TESTS: list[TrimTest] = [
    TrimTest(
        "custom_single_char",
        input="aaahelloaaa",
        chars="a",
        expected="hello",
        msg="$trim should trim occurrences of a single custom char from both ends",
    ),
    TrimTest(
        "custom_repeated_single",
        input="xxxhelloxxx",
        chars="x",
        expected="hello",
        msg="$trim should trim repeated custom char from both ends",
    ),
    # Custom chars completely replaces the default whitespace set.
    TrimTest(
        "custom_spaces_not_trimmed",
        input="  xxxhelloxxx  ",
        chars="x",
        expected="  xxxhelloxxx  ",
        msg="$trim should not trim spaces when custom chars replaces default set",
    ),
    TrimTest(
        "custom_tabs_not_trimmed",
        input="\t\txxxhelloxxx\t\t",
        chars="x",
        expected="\t\txxxhelloxxx\t\t",
        msg="$trim should not trim tabs when custom chars replaces default set",
    ),
    # Duplicate characters in chars have no additional effect.
    TrimTest(
        "custom_duplicate_chars",
        input="aaahelloaaa",
        chars="aab",
        expected="hello",
        msg="$trim should ignore duplicate characters in chars",
    ),
    # Each character in chars is treated individually, not as a substring pattern.
    TrimTest(
        "custom_individual_any_order",
        input="cbahelloabc",
        chars="abc",
        expected="hello",
        msg="$trim should treat each char in chars individually, not as a substring",
    ),
    TrimTest(
        "custom_individual_mixed_repeats",
        input="aabbcchelloccbbaa",
        chars="abc",
        expected="hello",
        msg="$trim should trim mixed repeats of individual chars from both ends",
    ),
    # Characters not in chars are preserved.
    TrimTest(
        "custom_no_match",
        input="xhellox",
        chars="a",
        expected="xhellox",
        msg="$trim should preserve chars not in the trim set",
    ),
    # Order of characters in chars does not affect the result.
    TrimTest(
        "custom_order_abc",
        input="bcaahelloaabc",
        chars="abc",
        expected="hello",
        msg="$trim should produce same result regardless of chars order (abc)",
    ),
    TrimTest(
        "custom_order_cba",
        input="bcaahelloaabc",
        chars="cba",
        expected="hello",
        msg="$trim should produce same result regardless of chars order (cba)",
    ),
    TrimTest(
        "custom_order_bac",
        input="bcaahelloaabc",
        chars="bac",
        expected="hello",
        msg="$trim should produce same result regardless of chars order (bac)",
    ),
]


# Property [Whitespace Subset Chars]: when chars is a subset of whitespace characters, only
# those specific whitespace characters are trimmed; other whitespace is preserved.
TRIM_WHITESPACE_SUBSET_TESTS: list[TrimTest] = [
    TrimTest(
        "subset_tab_only",
        input="\t hello \t",
        chars="\t",
        expected=" hello ",
        msg="$trim with chars=tab should trim only tabs, preserving spaces",
    ),
    TrimTest(
        "subset_space_tab",
        input=" \t\nhello\n\t ",
        chars=" \t",
        expected="\nhello\n",
        msg="$trim with chars=space+tab should preserve newlines",
    ),
    TrimTest(
        "subset_newline_only",
        input="\n\n hello \n\n",
        chars="\n",
        expected=" hello ",
        msg="$trim with chars=newline should trim only newlines, preserving spaces",
    ),
]

TRIM_CUSTOM_CHARS_ALL_TESTS = TRIM_CUSTOM_CHARS_TESTS + TRIM_WHITESPACE_SUBSET_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TRIM_CUSTOM_CHARS_ALL_TESTS))
def test_trim_custom_chars(collection, test_case: TrimTest):
    """Test $trim custom chars trimming."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
