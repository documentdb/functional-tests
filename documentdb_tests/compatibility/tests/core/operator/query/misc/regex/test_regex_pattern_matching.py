"""
Tests for $regex query operator pattern matching behavior.

Covers basic patterns (prefix, suffix, exact, substring, wildcard, alternation),
special regex features (quantifiers, anchors, word boundaries, lookahead/lookbehind,
backreferences, character classes), advanced patterns (named groups, named backreferences,
atomic groups, possessive quantifiers, conditional patterns, \\K reset match start),
empty/edge-case patterns, and special characters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS_STRINGS = [
    {"_id": 1, "a": "abc"},
    {"_id": 2, "a": "abcdef"},
    {"_id": 3, "a": "xyz"},
    {"_id": 4, "a": "xyzabc"},
    {"_id": 5, "a": ""},
]

BASIC_PATTERN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="exact_match",
        filter={"a": {"$regex": "^abc$"}},
        doc=DOCS_STRINGS,
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex ^abc$ should match only exact 'abc'",
    ),
    QueryTestCase(
        id="prefix_match",
        filter={"a": {"$regex": "^abc"}},
        doc=DOCS_STRINGS,
        expected=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "abcdef"}],
        msg="$regex ^abc should match strings starting with 'abc'",
    ),
    QueryTestCase(
        id="suffix_match",
        filter={"a": {"$regex": "abc$"}},
        doc=DOCS_STRINGS,
        expected=[{"_id": 1, "a": "abc"}, {"_id": 4, "a": "xyzabc"}],
        msg="$regex abc$ should match strings ending with 'abc'",
    ),
    QueryTestCase(
        id="substring_match",
        filter={"a": {"$regex": "abc"}},
        doc=DOCS_STRINGS,
        expected=[
            {"_id": 1, "a": "abc"},
            {"_id": 2, "a": "abcdef"},
            {"_id": 4, "a": "xyzabc"},
        ],
        msg="$regex abc should match any string containing 'abc'",
    ),
    QueryTestCase(
        id="wildcard_match_all",
        filter={"a": {"$regex": ".*"}},
        doc=DOCS_STRINGS,
        expected=DOCS_STRINGS,
        msg="$regex .* should match all strings including empty",
    ),
    QueryTestCase(
        id="alternation",
        filter={"a": {"$regex": "cat|dog"}},
        doc=[
            {"_id": 1, "a": "cat"},
            {"_id": 2, "a": "dog"},
            {"_id": 3, "a": "bird"},
        ],
        expected=[{"_id": 1, "a": "cat"}, {"_id": 2, "a": "dog"}],
        msg="$regex cat|dog should match either",
    ),
    QueryTestCase(
        id="character_class",
        filter={"a": {"$regex": "^[a-z]+$"}},
        doc=[
            {"_id": 1, "a": "abc"},
            {"_id": 2, "a": "ABC"},
            {"_id": 3, "a": "abc123"},
        ],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex ^[a-z]+$ should match only lowercase strings",
    ),
    QueryTestCase(
        id="negated_character_class",
        filter={"a": {"$regex": "^[^abc]+$"}},
        doc=[
            {"_id": 1, "a": "xyz"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "xya"},
        ],
        expected=[{"_id": 1, "a": "xyz"}],
        msg="$regex [^abc] should exclude characters a, b, c",
    ),
]

QUANTIFIER_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="quantifier_star",
        filter={"a": {"$regex": "^ab*c$"}},
        doc=[
            {"_id": 1, "a": "ac"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "abbc"},
        ],
        expected=[
            {"_id": 1, "a": "ac"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "abbc"},
        ],
        msg="$regex b* should match zero or more b's",
    ),
    QueryTestCase(
        id="quantifier_plus",
        filter={"a": {"$regex": "^ab+c$"}},
        doc=[
            {"_id": 1, "a": "ac"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "abbc"},
        ],
        expected=[{"_id": 2, "a": "abc"}, {"_id": 3, "a": "abbc"}],
        msg="$regex b+ should match one or more b's",
    ),
    QueryTestCase(
        id="quantifier_question",
        filter={"a": {"$regex": "^ab?c$"}},
        doc=[
            {"_id": 1, "a": "ac"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "abbc"},
        ],
        expected=[{"_id": 1, "a": "ac"}, {"_id": 2, "a": "abc"}],
        msg="$regex b? should match zero or one b",
    ),
    QueryTestCase(
        id="quantifier_exact_n",
        filter={"a": {"$regex": "^a{3}$"}},
        doc=[{"_id": 1, "a": "aa"}, {"_id": 2, "a": "aaa"}, {"_id": 3, "a": "aaaa"}],
        expected=[{"_id": 2, "a": "aaa"}],
        msg="$regex a{3} should match exactly 3 a's",
    ),
    QueryTestCase(
        id="quantifier_range",
        filter={"a": {"$regex": "^a{2,4}$"}},
        doc=[
            {"_id": 1, "a": "a"},
            {"_id": 2, "a": "aa"},
            {"_id": 3, "a": "aaa"},
            {"_id": 4, "a": "aaaa"},
            {"_id": 5, "a": "aaaaa"},
        ],
        expected=[
            {"_id": 2, "a": "aa"},
            {"_id": 3, "a": "aaa"},
            {"_id": 4, "a": "aaaa"},
        ],
        msg="$regex a{2,4} should match 2 to 4 a's",
    ),
]

SPECIAL_FEATURE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="escaped_dot_literal",
        filter={"a": {"$regex": "a\\.b"}},
        doc=[{"_id": 1, "a": "a.b"}, {"_id": 2, "a": "axb"}],
        expected=[{"_id": 1, "a": "a.b"}],
        msg="$regex with escaped dot should match literal dot only",
    ),
    QueryTestCase(
        id="word_boundary",
        filter={"a": {"$regex": "\\bcat\\b"}},
        doc=[
            {"_id": 1, "a": "the cat sat"},
            {"_id": 2, "a": "concatenate"},
        ],
        expected=[{"_id": 1, "a": "the cat sat"}],
        msg="$regex \\bcat\\b should match whole word only",
    ),
    QueryTestCase(
        id="lookahead",
        filter={"a": {"$regex": "foo(?=bar)"}},
        doc=[{"_id": 1, "a": "foobar"}, {"_id": 2, "a": "foobaz"}],
        expected=[{"_id": 1, "a": "foobar"}],
        msg="$regex with lookahead (?=bar) should match foo only before bar",
    ),
    QueryTestCase(
        id="negative_lookahead",
        filter={"a": {"$regex": "foo(?!bar)"}},
        doc=[{"_id": 1, "a": "foobar"}, {"_id": 2, "a": "foobaz"}],
        expected=[{"_id": 2, "a": "foobaz"}],
        msg="$regex with negative lookahead (?!bar) should match foo not before bar",
    ),
    QueryTestCase(
        id="lookbehind",
        filter={"a": {"$regex": "(?<=foo)bar"}},
        doc=[{"_id": 1, "a": "foobar"}, {"_id": 2, "a": "bazbar"}],
        expected=[{"_id": 1, "a": "foobar"}],
        msg="$regex with lookbehind (?<=foo) should match bar only after foo",
    ),
    QueryTestCase(
        id="negative_lookbehind",
        filter={"a": {"$regex": "(?<!foo)bar"}},
        doc=[{"_id": 1, "a": "foobar"}, {"_id": 2, "a": "bazbar"}],
        expected=[{"_id": 2, "a": "bazbar"}],
        msg="$regex with negative lookbehind should match bar not after foo",
    ),
    QueryTestCase(
        id="non_capturing_group",
        filter={"a": {"$regex": "^(?:abc)+$"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "abcabc"}, {"_id": 3, "a": "ab"}],
        expected=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "abcabc"}],
        msg="$regex with non-capturing group (?:abc)+ should match",
    ),
    QueryTestCase(
        id="backreference",
        filter={"a": {"$regex": "^(abc)\\1$"}},
        doc=[{"_id": 1, "a": "abcabc"}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 1, "a": "abcabc"}],
        msg="$regex with backreference (abc)\\1 should match 'abcabc'",
    ),
    QueryTestCase(
        id="character_class_d",
        filter={"a": {"$regex": "^\\d+$"}},
        doc=[{"_id": 1, "a": "123"}, {"_id": 2, "a": "abc"}, {"_id": 3, "a": "12a"}],
        expected=[{"_id": 1, "a": "123"}],
        msg="$regex \\d+ should match digits only",
    ),
    QueryTestCase(
        id="character_class_w",
        filter={"a": {"$regex": "^\\w+$"}},
        doc=[{"_id": 1, "a": "abc_123"}, {"_id": 2, "a": "abc 123"}],
        expected=[{"_id": 1, "a": "abc_123"}],
        msg="$regex \\w+ should match word characters",
    ),
    QueryTestCase(
        id="character_class_s",
        filter={"a": {"$regex": "\\s"}},
        doc=[{"_id": 1, "a": "hello world"}, {"_id": 2, "a": "helloworld"}],
        expected=[{"_id": 1, "a": "hello world"}],
        msg="$regex \\s should match whitespace",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_pattern_matches_all",
        filter={"a": {"$regex": ""}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": ""}],
        expected=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": ""}],
        msg="$regex with empty string should match all string fields",
    ),
    QueryTestCase(
        id="caret_dollar_matches_empty",
        filter={"a": {"$regex": "^$"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": ""}],
        expected=[{"_id": 2, "a": ""}],
        msg="$regex ^$ should match only empty string",
    ),
    QueryTestCase(
        id="caret_only_matches_all",
        filter={"a": {"$regex": "^"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": ""}],
        expected=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": ""}],
        msg="$regex ^ should match all strings",
    ),
    QueryTestCase(
        id="deeply_nested_groups",
        filter={"a": {"$regex": "^((((a))))$"}},
        doc=[{"_id": 1, "a": "a"}, {"_id": 2, "a": "b"}],
        expected=[{"_id": 1, "a": "a"}],
        msg="$regex with deeply nested groups should work",
    ),
    QueryTestCase(
        id="max_pattern_length_accepted",
        filter={"a": {"$regex": "a" * 16384}},
        doc=[{"_id": 1, "a": "abc"}],
        expected=[],
        msg="$regex at max pattern length should be accepted",
    ),
]

ADVANCED_PATTERN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="named_capture_group",
        filter={"a": {"$regex": "(?P<word>abc)"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with named capture group (?P<word>...) should match",
    ),
    QueryTestCase(
        id="named_backreference",
        filter={"a": {"$regex": "(?P<word>abc)-(?P=word)"}},
        doc=[{"_id": 1, "a": "abc-abc"}, {"_id": 2, "a": "abc-xyz"}],
        expected=[{"_id": 1, "a": "abc-abc"}],
        msg="$regex with named backreference (?P=word) should match repeated group",
    ),
    QueryTestCase(
        id="atomic_group",
        filter={"a": {"$regex": "^(?>abc)+$"}},
        doc=[{"_id": 1, "a": "abcabc"}, {"_id": 2, "a": "abc"}, {"_id": 3, "a": "ab"}],
        expected=[{"_id": 1, "a": "abcabc"}, {"_id": 2, "a": "abc"}],
        msg="$regex with atomic group (?>abc)+ should match",
    ),
    QueryTestCase(
        id="possessive_quantifier",
        filter={"a": {"$regex": "a++b"}},
        doc=[{"_id": 1, "a": "aaab"}, {"_id": 2, "a": "bbb"}],
        expected=[{"_id": 1, "a": "aaab"}],
        msg="$regex with possessive quantifier a++ should match",
    ),
    QueryTestCase(
        id="lazy_quantifier_plus",
        filter={"a": {"$regex": "a.+?b"}},
        doc=[{"_id": 1, "a": "aXb"}, {"_id": 2, "a": "ab"}, {"_id": 3, "a": "cd"}],
        expected=[{"_id": 1, "a": "aXb"}],
        msg="$regex with lazy quantifier .+? should match non-greedy",
    ),
    QueryTestCase(
        id="anchor_A_start",
        filter={"a": {"$regex": "\\Aabc"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "xabc"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with \\A anchor should match start of string",
    ),
    QueryTestCase(
        id="anchor_Z_end",
        filter={"a": {"$regex": "abc\\Z"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "abcx"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex with \\Z anchor should match end of string",
    ),
    QueryTestCase(
        id="non_word_boundary_B",
        filter={"a": {"$regex": "\\Bcat"}},
        doc=[{"_id": 1, "a": "concatenate"}, {"_id": 2, "a": "cat sat"}],
        expected=[{"_id": 1, "a": "concatenate"}],
        msg="$regex \\Bcat should match cat NOT at word boundary",
    ),
    QueryTestCase(
        id="conditional_pattern_match",
        filter={"a": {"$regex": "^(a)?(?(1)b|c)$"}},
        doc=[
            {"_id": 1, "a": "ab"},
            {"_id": 2, "a": "c"},
            {"_id": 3, "a": "ac"},
            {"_id": 4, "a": "b"},
        ],
        expected=[{"_id": 1, "a": "ab"}, {"_id": 2, "a": "c"}],
        msg="$regex conditional (?(1)b|c) should match 'ab' when group 1 captured, 'c' otherwise",
    ),
    QueryTestCase(
        id="reset_match_start_K",
        filter={"a": {"$regex": "foo\\Kbar"}},
        doc=[{"_id": 1, "a": "foobar"}, {"_id": 2, "a": "bar"}, {"_id": 3, "a": "foo"}],
        expected=[{"_id": 1, "a": "foobar"}],
        msg="$regex with \\K should match foobar "
        "(\\K resets match start but still requires foo before bar)",
    ),
]

DATE_STRING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="date_format_match",
        filter={"a": {"$regex": "^\\d{4}-\\d{2}-\\d{2}$"}},
        doc=[
            {"_id": 1, "a": "2024-01-15"},
            {"_id": 2, "a": "not a date"},
            {"_id": 3, "a": "2024/01/15"},
        ],
        expected=[{"_id": 1, "a": "2024-01-15"}],
        msg="$regex should match date-formatted strings",
    ),
]

SPECIAL_CHAR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="escaped_asterisk",
        filter={"a": {"$regex": "a\\*b"}},
        doc=[{"_id": 1, "a": "a*b"}, {"_id": 2, "a": "ab"}],
        expected=[{"_id": 1, "a": "a*b"}],
        msg="$regex with escaped asterisk should match literal *",
    ),
    QueryTestCase(
        id="escaped_plus",
        filter={"a": {"$regex": "a\\+b"}},
        doc=[{"_id": 1, "a": "a+b"}, {"_id": 2, "a": "ab"}],
        expected=[{"_id": 1, "a": "a+b"}],
        msg="$regex with escaped plus should match literal +",
    ),
    QueryTestCase(
        id="escaped_question",
        filter={"a": {"$regex": "a\\?b"}},
        doc=[{"_id": 1, "a": "a?b"}, {"_id": 2, "a": "ab"}],
        expected=[{"_id": 1, "a": "a?b"}],
        msg="$regex with escaped question mark should match literal ?",
    ),
    QueryTestCase(
        id="escaped_caret",
        filter={"a": {"$regex": "\\^abc"}},
        doc=[{"_id": 1, "a": "^abc"}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 1, "a": "^abc"}],
        msg="$regex with escaped caret should match literal ^",
    ),
    QueryTestCase(
        id="escaped_dollar",
        filter={"a": {"$regex": "abc\\$"}},
        doc=[{"_id": 1, "a": "abc$"}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 1, "a": "abc$"}],
        msg="$regex with escaped dollar should match literal $",
    ),
    QueryTestCase(
        id="escaped_pipe",
        filter={"a": {"$regex": "a\\|b"}},
        doc=[{"_id": 1, "a": "a|b"}, {"_id": 2, "a": "a"}, {"_id": 3, "a": "b"}],
        expected=[{"_id": 1, "a": "a|b"}],
        msg="$regex with escaped pipe should match literal |",
    ),
    QueryTestCase(
        id="escaped_backslash",
        filter={"a": {"$regex": "a\\\\b"}},
        doc=[{"_id": 1, "a": "a\\b"}, {"_id": 2, "a": "ab"}],
        expected=[{"_id": 1, "a": "a\\b"}],
        msg="$regex with escaped backslash should match literal \\",
    ),
]

ALL_TESTS = (
    BASIC_PATTERN_TESTS
    + QUANTIFIER_TESTS
    + SPECIAL_FEATURE_TESTS
    + EDGE_CASE_TESTS
    + ADVANCED_PATTERN_TESTS
    + DATE_STRING_TESTS
    + SPECIAL_CHAR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_regex_pattern_matching(collection, test):
    """Parametrized test for $regex pattern matching behavior."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
