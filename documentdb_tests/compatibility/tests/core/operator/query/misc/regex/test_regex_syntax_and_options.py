"""
Tests for $regex query operator syntax variations and options.

Covers all syntax forms (string, regex object, implicit, $options),
option flags (i, m, s, x, u), PCRE inline toggles, inline flags
((?m), (?s), (?x)), and scoped flags ((?i:...), (?s:...), (?m:...)).
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS_BASIC = [
    {"_id": 1, "a": "apple"},
    {"_id": 2, "a": "APPLE"},
    {"_id": 3, "a": "banana"},
]

SYNTAX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_pattern",
        filter={"a": {"$regex": "^app"}},
        doc=DOCS_BASIC,
        expected=[{"_id": 1, "a": "apple"}],
        msg="$regex with string pattern should match",
    ),
    QueryTestCase(
        id="regex_object",
        filter={"a": {"$regex": Regex("^app")}},
        doc=DOCS_BASIC,
        expected=[{"_id": 1, "a": "apple"}],
        msg="$regex with regex object should match",
    ),
    QueryTestCase(
        id="implicit_regex",
        filter={"a": Regex("^app")},
        doc=DOCS_BASIC,
        expected=[{"_id": 1, "a": "apple"}],
        msg="Implicit regex shorthand should match",
    ),
    QueryTestCase(
        id="implicit_regex_with_flag",
        filter={"a": Regex("^app", "i")},
        doc=DOCS_BASIC,
        expected=[{"_id": 1, "a": "apple"}, {"_id": 2, "a": "APPLE"}],
        msg="Implicit regex with inline 'i' flag should match case-insensitively",
    ),
    QueryTestCase(
        id="string_with_options",
        filter={"a": {"$regex": "^app", "$options": "i"}},
        doc=DOCS_BASIC,
        expected=[{"_id": 1, "a": "apple"}, {"_id": 2, "a": "APPLE"}],
        msg="$regex string with $options 'i' should match case-insensitively",
    ),
    QueryTestCase(
        id="regex_object_with_options",
        filter={"a": {"$regex": Regex("^app"), "$options": "i"}},
        doc=DOCS_BASIC,
        expected=[{"_id": 1, "a": "apple"}, {"_id": 2, "a": "APPLE"}],
        msg="$regex regex object (no flags) with $options 'i' should match case-insensitively",
    ),
    QueryTestCase(
        id="reversed_key_order_options_before_regex",
        filter={"a": {"$options": "i", "$regex": "^app"}},
        doc=DOCS_BASIC,
        expected=[{"_id": 1, "a": "apple"}, {"_id": 2, "a": "APPLE"}],
        msg="$options before $regex (reversed key order, no conflict) should match "
        "case-insensitively",
    ),
]

CASE_INSENSITIVE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="i_flag_matches_mixed_case",
        filter={"a": {"$regex": "^ABC", "$options": "i"}},
        doc=[
            {"_id": 1, "a": "abc123"},
            {"_id": 2, "a": "ABC123"},
            {"_id": 3, "a": "Abc123"},
            {"_id": 4, "a": "xyz"},
        ],
        expected=[
            {"_id": 1, "a": "abc123"},
            {"_id": 2, "a": "ABC123"},
            {"_id": 3, "a": "Abc123"},
        ],
        msg="$regex with 'i' should match all case variants",
    ),
    QueryTestCase(
        id="no_i_flag_case_sensitive",
        filter={"a": {"$regex": "^ABC"}},
        doc=[{"_id": 1, "a": "abc123"}, {"_id": 2, "a": "ABC123"}],
        expected=[{"_id": 2, "a": "ABC123"}],
        msg="$regex without 'i' should be case-sensitive",
    ),
    QueryTestCase(
        id="pcre_inline_case_insensitive",
        filter={"a": {"$regex": "(?i)abc"}},
        doc=[{"_id": 1, "a": "ABC"}, {"_id": 2, "a": "abc"}, {"_id": 3, "a": "xyz"}],
        expected=[{"_id": 1, "a": "ABC"}, {"_id": 2, "a": "abc"}],
        msg="PCRE inline (?i) should match case-insensitively",
    ),
    QueryTestCase(
        id="pcre_toggle_case_insensitive",
        filter={"a": {"$regex": "(?i)a(?-i)bc"}},
        doc=[
            {"_id": 1, "a": "abc"},
            {"_id": 2, "a": "Abc"},
            {"_id": 3, "a": "aBC"},
        ],
        expected=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "Abc"}],
        msg="PCRE toggle (?i)a(?-i)bc should match abc/Abc but not aBC",
    ),
    QueryTestCase(
        id="i_flag_non_ascii_cafe",
        filter={"a": {"$regex": "^CAFÉ", "$options": "i"}},
        doc=[
            {"_id": 1, "a": "café"},
            {"_id": 2, "a": "CAFÉ"},
            {"_id": 3, "a": "xyz"},
        ],
        expected=[{"_id": 1, "a": "café"}, {"_id": 2, "a": "CAFÉ"}],
        msg="$regex /^CAFÉ/i should match case-insensitively with non-ASCII",
    ),
]

MULTILINE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="m_flag_caret_matches_after_newline",
        filter={"a": {"$regex": "^S", "$options": "m"}},
        doc=[{"_id": 1, "a": "First line\nSecond line"}, {"_id": 2, "a": "No match"}],
        expected=[{"_id": 1, "a": "First line\nSecond line"}],
        msg="$regex /^S/m should match S at start of second line",
    ),
    QueryTestCase(
        id="no_m_flag_caret_only_start",
        filter={"a": {"$regex": "^S"}},
        doc=[{"_id": 1, "a": "First line\nSecond line"}, {"_id": 2, "a": "Second"}],
        expected=[{"_id": 2, "a": "Second"}],
        msg="$regex /^S/ without m should only match start of string",
    ),
    QueryTestCase(
        id="m_flag_dollar_matches_before_newline",
        filter={"a": {"$regex": "line$", "$options": "m"}},
        doc=[{"_id": 1, "a": "First line\nSecond"}, {"_id": 2, "a": "no match"}],
        expected=[{"_id": 1, "a": "First line\nSecond"}],
        msg="$regex /line$/m should match line at end of first line",
    ),
    QueryTestCase(
        id="m_flag_no_newlines_same_as_without",
        filter={"a": {"$regex": "^S", "$options": "m"}},
        doc=[{"_id": 1, "a": "Start"}, {"_id": 2, "a": "no"}],
        expected=[{"_id": 1, "a": "Start"}],
        msg="$regex /^S/m on string without newlines should behave same as without m",
    ),
]

DOTALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="s_flag_dot_matches_newline",
        filter={"a": {"$regex": "M.*line", "$options": "s"}},
        doc=[{"_id": 1, "a": "Multiple\nline"}, {"_id": 2, "a": "no match"}],
        expected=[{"_id": 1, "a": "Multiple\nline"}],
        msg="$regex with 's' should make dot match newline",
    ),
    QueryTestCase(
        id="no_s_flag_dot_stops_at_newline",
        filter={"a": {"$regex": "M.*line"}},
        doc=[{"_id": 1, "a": "Multiple\nline"}, {"_id": 2, "a": "Mainline"}],
        expected=[{"_id": 2, "a": "Mainline"}],
        msg="$regex without 's' dot should not match newline",
    ),
    QueryTestCase(
        id="s_and_i_combined",
        filter={"a": {"$regex": "MULTI.*LINE", "$options": "si"}},
        doc=[{"_id": 1, "a": "Multiple\nline"}, {"_id": 2, "a": "no"}],
        expected=[{"_id": 1, "a": "Multiple\nline"}],
        msg="$regex with 'si' should combine dot-all and case-insensitive",
    ),
]

EXTENDED_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="x_flag_ignores_whitespace",
        filter={"a": {"$regex": "a b c", "$options": "x"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "a b c"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with 'x' should ignore unescaped whitespace in pattern",
    ),
    QueryTestCase(
        id="x_flag_ignores_comments",
        filter={"a": {"$regex": "abc #comment\n123", "$options": "x"}},
        doc=[{"_id": 1, "a": "abc123"}, {"_id": 2, "a": "abc #comment 123"}],
        expected=[{"_id": 1, "a": "abc123"}],
        msg="$regex with 'x' should ignore comments after #",
    ),
    QueryTestCase(
        id="x_flag_space_in_char_class_preserved",
        filter={"a": {"$regex": "[a b]", "$options": "x"}},
        doc=[
            {"_id": 1, "a": "a"},
            {"_id": 2, "a": " "},
            {"_id": 3, "a": "b"},
            {"_id": 4, "a": "c"},
        ],
        expected=[
            {"_id": 1, "a": "a"},
            {"_id": 2, "a": " "},
            {"_id": 3, "a": "b"},
        ],
        msg="$regex with 'x' should preserve space inside character class",
    ),
]

UNICODE_OPTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="u_option_accepted",
        filter={"a": {"$regex": "abc", "$options": "u"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with 'u' option should be accepted (redundant but valid)",
    ),
]

INLINE_FLAG_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="pcre_inline_multiline",
        filter={"a": {"$regex": "(?m)^S"}},
        doc=[{"_id": 1, "a": "First line\nSecond line"}, {"_id": 2, "a": "No match"}],
        expected=[{"_id": 1, "a": "First line\nSecond line"}],
        msg="PCRE inline (?m) should make ^ match after newline",
    ),
    QueryTestCase(
        id="pcre_inline_dotall",
        filter={"a": {"$regex": "(?s)M.*line"}},
        doc=[{"_id": 1, "a": "Multiple\nline"}, {"_id": 2, "a": "no match"}],
        expected=[{"_id": 1, "a": "Multiple\nline"}],
        msg="PCRE inline (?s) should make dot match newline",
    ),
    QueryTestCase(
        id="pcre_inline_extended",
        filter={"a": {"$regex": "(?x)a b c"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "a b c"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="PCRE inline (?x) should ignore unescaped whitespace in pattern",
    ),
]

SCOPED_FLAG_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="scoped_case_insensitive",
        filter={"a": {"$regex": "(?i:abc)def"}},
        doc=[
            {"_id": 1, "a": "ABCdef"},
            {"_id": 2, "a": "abcdef"},
            {"_id": 3, "a": "abcDEF"},
        ],
        expected=[{"_id": 1, "a": "ABCdef"}, {"_id": 2, "a": "abcdef"}],
        msg="$regex (?i:abc)def should apply case-insensitive only to abc, not def",
    ),
    QueryTestCase(
        id="scoped_dotall",
        filter={"a": {"$regex": "(?s:a.b)c"}},
        doc=[
            {"_id": 1, "a": "a\nbc"},
            {"_id": 2, "a": "axbc"},
            {"_id": 3, "a": "a\nc"},
        ],
        expected=[{"_id": 1, "a": "a\nbc"}, {"_id": 2, "a": "axbc"}],
        msg="$regex (?s:a.b)c should apply dotall only inside the group",
    ),
    QueryTestCase(
        id="scoped_multiline",
        filter={"a": {"$regex": "(?m:^S).*end"}},
        doc=[
            {"_id": 1, "a": "First\nStart end"},
            {"_id": 2, "a": "no match"},
        ],
        expected=[{"_id": 1, "a": "First\nStart end"}],
        msg="$regex (?m:^S) should apply multiline only inside the group",
    ),
]

OPTIONS_VALID_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="options_empty_string",
        filter={"a": {"$regex": "abc", "$options": ""}},
        doc=[{"_id": 1, "a": "abc"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with empty $options should succeed",
    ),
    QueryTestCase(
        id="options_im_combined",
        filter={"a": {"$regex": "^abc", "$options": "im"}},
        doc=[{"_id": 1, "a": "hello\nABC"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 1, "a": "hello\nABC"}],
        msg="$regex with 'im' should combine case-insensitive and multiline",
    ),
    QueryTestCase(
        id="options_ixms_all_combined",
        filter={"a": {"$regex": "a b c", "$options": "ixms"}},
        doc=[{"_id": 1, "a": "ABC"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 1, "a": "ABC"}],
        msg="$regex with 'ixms' should combine all options",
    ),
    QueryTestCase(
        id="options_duplicate_ii",
        filter={"a": {"$regex": "abc", "$options": "ii"}},
        doc=[{"_id": 1, "a": "ABC"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 1, "a": "ABC"}],
        msg="$regex with duplicate 'ii' should succeed (no error)",
    ),
    QueryTestCase(
        id="m_flag_crlf_line_endings",
        filter={"a": {"$regex": "^S", "$options": "m"}},
        doc=[{"_id": 1, "a": "First\r\nSecond"}, {"_id": 2, "a": "no"}],
        expected=[{"_id": 1, "a": "First\r\nSecond"}],
        msg="$regex /^S/m should match after \\r\\n line endings",
    ),
    QueryTestCase(
        id="x_flag_hash_in_char_class",
        filter={"a": {"$regex": "[a#b]", "$options": "x"}},
        doc=[{"_id": 1, "a": "#"}, {"_id": 2, "a": "a"}, {"_id": 3, "a": "c"}],
        expected=[{"_id": 1, "a": "#"}, {"_id": 2, "a": "a"}],
        msg="$regex with 'x' should treat # in char class as literal",
    ),
    QueryTestCase(
        id="x_flag_escaped_space",
        filter={"a": {"$regex": "a\\ b", "$options": "x"}},
        doc=[{"_id": 1, "a": "a b"}, {"_id": 2, "a": "ab"}],
        expected=[{"_id": 1, "a": "a b"}],
        msg="$regex with 'x' should preserve escaped space",
    ),
]

ALL_SUCCESS_TESTS = (
    SYNTAX_TESTS
    + CASE_INSENSITIVE_TESTS
    + MULTILINE_TESTS
    + DOTALL_TESTS
    + EXTENDED_TESTS
    + UNICODE_OPTION_TESTS
    + INLINE_FLAG_TESTS
    + SCOPED_FLAG_TESTS
    + OPTIONS_VALID_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_SUCCESS_TESTS))
def test_regex_syntax_and_options(collection, test):
    """Parametrized test for $regex syntax variations and option flags."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
