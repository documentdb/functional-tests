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

# Property [Special Characters]: null bytes, control characters, punctuation,
# braces, brackets, quotes, and regex-special characters are treated as literal
# string content. Dollar signs must be passed via $literal.
REPLACEONE_SPECIAL_CHAR_TESTS: list[ReplaceOneTest] = [
    # Control character U+0001 (SOH) in input.
    ReplaceOneTest(
        "special_control_soh",
        input="a\x01b",
        find="\x01",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special control soh",
    ),
    # Control character U+001F (US) in input.
    ReplaceOneTest(
        "special_control_us",
        input="a\x1fb",
        find="\x1f",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special control us",
    ),
    # Control character in find position.
    ReplaceOneTest(
        "special_control_find_no_match",
        input="hello",
        find="\x01",
        replacement="X",
        expected="hello",
        msg="$replaceOne special control find no match",
    ),
    # Control character in replacement position.
    ReplaceOneTest(
        "special_control_replacement",
        input="aXb",
        find="X",
        replacement="\x01",
        expected="a\x01b",
        msg="$replaceOne special control replacement",
    ),
    # Null byte (U+0000) treated as regular string content.
    ReplaceOneTest(
        "special_null_byte",
        input="a\x00b",
        find="\x00",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special null byte",
    ),
    # Null byte in replacement position.
    ReplaceOneTest(
        "special_null_byte_replacement",
        input="aXb",
        find="X",
        replacement="\x00",
        expected="a\x00b",
        msg="$replaceOne special null byte replacement",
    ),
    # Braces treated as literal data.
    ReplaceOneTest(
        "special_braces",
        input="a{b}c",
        find="{b}",
        replacement="X",
        expected="aXc",
        msg="$replaceOne special braces",
    ),
    # Brackets treated as literal data.
    ReplaceOneTest(
        "special_brackets",
        input="a[b]c",
        find="[b]",
        replacement="X",
        expected="aXc",
        msg="$replaceOne special brackets",
    ),
    # Double quotes treated as literal data.
    ReplaceOneTest(
        "special_double_quotes",
        input='a"b"c',
        find='"b"',
        replacement="X",
        expected="aXc",
        msg="$replaceOne special double quotes",
    ),
    # Single quotes treated as literal data.
    ReplaceOneTest(
        "special_single_quotes",
        input="a'b'c",
        find="'b'",
        replacement="X",
        expected="aXc",
        msg="$replaceOne special single quotes",
    ),
    # General punctuation treated as literal data.
    ReplaceOneTest(
        "special_punctuation",
        input="a!@#%&b",
        find="!@#%&",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special punctuation",
    ),
    # Backslash treated as literal data.
    ReplaceOneTest(
        "special_backslash",
        input="a\\b",
        find="\\",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special backslash",
    ),
    # Backslash in replacement position.
    ReplaceOneTest(
        "special_backslash_replacement",
        input="hello",
        find="h",
        replacement="\\",
        expected="\\ello",
        msg="$replaceOne special backslash replacement",
    ),
    # Backslash in both input and find.
    ReplaceOneTest(
        "special_backslash_in_input_and_find",
        input="a\\b",
        find="a\\b",
        replacement="X",
        expected="X",
        msg="$replaceOne special backslash in input and find",
    ),
    # Regex ? treated as literal.
    ReplaceOneTest(
        "special_regex_question",
        input="a?b",
        find="?",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special regex question",
    ),
    # Regex ^ treated as literal.
    ReplaceOneTest(
        "special_regex_caret",
        input="a^b",
        find="^",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special regex caret",
    ),
    # Regex | treated as literal.
    ReplaceOneTest(
        "special_regex_pipe",
        input="a|b",
        find="|",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special regex pipe",
    ),
    # Regex \d treated as literal two-character sequence.
    ReplaceOneTest(
        "special_regex_backslash_d",
        input="a\\db",
        find="\\d",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special regex backslash d",
    ),
    # Regex . treated as literal.
    ReplaceOneTest(
        "special_regex_dot",
        input="total: 10.00 dollars",
        find="10.00",
        replacement="20.00",
        expected="total: 20.00 dollars",
        msg="$replaceOne special regex dot",
    ),
    # Regex .* treated as literal.
    ReplaceOneTest(
        "special_regex_dot_star",
        input="a.*b",
        find=".*",
        replacement="X",
        expected="aXb",
        msg="$replaceOne special regex dot star",
    ),
    # Regex (, ), + treated as literal.
    ReplaceOneTest(
        "special_regex_parens_plus",
        input="(a+b)",
        find="(a+b)",
        replacement="X",
        expected="X",
        msg="$replaceOne special regex parens plus",
    ),
    # Dollar sign via $literal in input and find.
    ReplaceOneTest(
        "special_dollar_literal_input",
        input={"$literal": "$100"},
        find={"$literal": "$"},
        replacement="USD",
        expected="USD100",
        msg="$replaceOne special dollar literal input",
    ),
    # Dollar sign via $literal in find.
    ReplaceOneTest(
        "special_dollar_literal_find",
        input="price: $100",
        find={"$literal": "$"},
        replacement="USD",
        expected="price: USD100",
        msg="$replaceOne special dollar literal find",
    ),
    # Dollar sign via $literal in replacement.
    ReplaceOneTest(
        "special_dollar_literal_replacement",
        input="price: USD100",
        find="USD",
        replacement={"$literal": "$"},
        expected="price: $100",
        msg="$replaceOne special dollar literal replacement",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_SPECIAL_CHAR_TESTS))
def test_replaceone_special_char_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne special character cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
