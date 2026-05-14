"""
Tests for $regex query operator Unicode and encoding behavior.

Covers Unicode character matching, *UCP option for UTF-8 word boundaries,
Unicode character properties (\\p{Latin}, \\p{L}), negated properties (\\P{L}),
POSIX character classes with Unicode, Cyrillic case-insensitive matching,
\\w/\\d behavior with and without *UCP, NFC/NFD normalization behavior,
and case folding edge cases (Turkish İ, German ß).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UNICODE_DOCS = [
    {"_id": 1, "a": "hello"},
    {"_id": 2, "a": "café"},
    {"_id": 3, "a": "naïve"},
    {"_id": 4, "a": "日本語"},
    {"_id": 5, "a": "Привет"},
    {"_id": 6, "a": "你好"},
]

UNICODE_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="ascii_match",
        filter={"a": {"$regex": "hello"}},
        doc=UNICODE_DOCS,
        expected=[{"_id": 1, "a": "hello"}],
        msg="$regex should match ASCII characters",
    ),
    QueryTestCase(
        id="accented_char_match",
        filter={"a": {"$regex": "café"}},
        doc=UNICODE_DOCS,
        expected=[{"_id": 2, "a": "café"}],
        msg="$regex should match accented characters",
    ),
    QueryTestCase(
        id="cjk_japanese_match",
        filter={"a": {"$regex": "日本"}},
        doc=UNICODE_DOCS,
        expected=[{"_id": 4, "a": "日本語"}],
        msg="$regex should match Japanese CJK characters",
    ),
    QueryTestCase(
        id="cjk_chinese_match",
        filter={"a": {"$regex": "你好"}},
        doc=UNICODE_DOCS,
        expected=[{"_id": 6, "a": "你好"}],
        msg="$regex should match Chinese CJK characters",
    ),
    QueryTestCase(
        id="cyrillic_exact_case",
        filter={"a": {"$regex": "Привет"}},
        doc=UNICODE_DOCS,
        expected=[{"_id": 5, "a": "Привет"}],
        msg="$regex should match Cyrillic characters exact case",
    ),
    QueryTestCase(
        id="cyrillic_case_insensitive",
        filter={"a": {"$regex": "привет", "$options": "i"}},
        doc=UNICODE_DOCS,
        expected=[{"_id": 5, "a": "Привет"}],
        msg="$regex with 'i' should match Cyrillic case-insensitively",
    ),
]

UCP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="ucp_word_boundary_respects_unicode",
        filter={"a": {"$regex": "(*UCP)\\byster"}},
        doc=[{"_id": 1, "a": "Blue Öyster Cult"}, {"_id": 2, "a": "oyster"}],
        expected=[],
        msg="(*UCP)\\byster should not match — UCP treats Ö as word char so no boundary before y",
    ),
    QueryTestCase(
        id="no_ucp_word_boundary_ignores_unicode",
        filter={"a": {"$regex": "\\byster"}},
        doc=[{"_id": 1, "a": "Blue Öyster Cult"}, {"_id": 2, "a": "oyster"}],
        expected=[{"_id": 1, "a": "Blue Öyster Cult"}],
        msg="\\byster without UCP should match after Ö (Ö not treated as word char)",
    ),
    QueryTestCase(
        id="ucp_w_matches_unicode_word_chars",
        filter={"a": {"$regex": "(*UCP)^\\w+$"}},
        doc=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": "café"},
            {"_id": 3, "a": "日本語"},
            {"_id": 4, "a": "hello world"},
            {"_id": 5, "a": "你好"},
        ],
        expected=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": "café"},
            {"_id": 3, "a": "日本語"},
            {"_id": 5, "a": "你好"},
        ],
        msg="(*UCP)\\w+ should match all Unicode word characters",
    ),
    QueryTestCase(
        id="no_ucp_w_ascii_only",
        filter={"a": {"$regex": "^\\w+$"}},
        doc=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": "café"},
            {"_id": 3, "a": "日本語"},
            {"_id": 4, "a": "你好"},
        ],
        expected=[{"_id": 1, "a": "hello"}],
        msg="\\w+ without UCP should match ASCII word characters only",
    ),
]

UNICODE_PROPERTY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="unicode_property_latin",
        filter={"a": {"$regex": "\\p{Latin}"}},
        doc=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": "日本語"},
            {"_id": 3, "a": "123"},
        ],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$regex \\p{Latin} should match Latin script characters",
    ),
    QueryTestCase(
        id="unicode_property_any_letter",
        filter={"a": {"$regex": "\\p{L}"}},
        doc=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": "日本語"},
            {"_id": 3, "a": "123"},
            {"_id": 4, "a": "你好"},
        ],
        expected=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": "日本語"}, {"_id": 4, "a": "你好"}],
        msg="$regex \\p{L} should match any Unicode letter",
    ),
    QueryTestCase(
        id="unicode_property_cyrillic",
        filter={"a": {"$regex": "^\\p{Cyrillic}+$"}},
        doc=[
            {"_id": 1, "a": "Привет"},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": "123"},
        ],
        expected=[{"_id": 1, "a": "Привет"}],
        msg="$regex \\p{Cyrillic} should match Cyrillic script characters",
    ),
    QueryTestCase(
        id="unicode_property_han",
        filter={"a": {"$regex": "^\\p{Han}+$"}},
        doc=[
            {"_id": 1, "a": "你好"},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": "123"},
        ],
        expected=[{"_id": 1, "a": "你好"}],
        msg="$regex \\p{Han} should match CJK Han characters",
    ),
    QueryTestCase(
        id="unicode_property_digit_Nd",
        filter={"a": {"$regex": "^\\p{Nd}+$"}},
        doc=[
            {"_id": 1, "a": "123"},
            {"_id": 2, "a": "\u0661\u0662\u0663"},
            {"_id": 3, "a": "abc"},
        ],
        expected=[{"_id": 1, "a": "123"}, {"_id": 2, "a": "\u0661\u0662\u0663"}],
        msg="$regex \\p{Nd} should match any Unicode decimal digit",
    ),
]

UTF_PREFIX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="utf_prefix_matches",
        filter={"a": {"$regex": "(*UTF)café"}},
        doc=[{"_id": 1, "a": "café"}, {"_id": 2, "a": "cafe"}],
        expected=[{"_id": 1, "a": "café"}],
        msg="$regex with (*UTF) prefix should match Unicode",
    ),
    QueryTestCase(
        id="utf_prefix_cjk",
        filter={"a": {"$regex": "(*UTF)你好"}},
        doc=[{"_id": 1, "a": "你好"}, {"_id": 2, "a": "hello"}],
        expected=[{"_id": 1, "a": "你好"}],
        msg="$regex with (*UTF) prefix should match CJK characters",
    ),
    QueryTestCase(
        id="utf_prefix_dot_matches_multibyte",
        filter={"a": {"$regex": "(*UTF)^.{2}$"}},
        doc=[{"_id": 1, "a": "你好"}, {"_id": 2, "a": "a"}],
        expected=[{"_id": 1, "a": "你好"}],
        msg="$regex with (*UTF) should treat multibyte chars as single code points for dot",
    ),
]

POSIX_CLASS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="posix_alpha_ascii",
        filter={"a": {"$regex": "[[:alpha:]]"}},
        doc=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": "123"},
        ],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$regex [:alpha:] should match ASCII alphabetic by default",
    ),
    QueryTestCase(
        id="posix_alpha_ucp",
        filter={"a": {"$regex": "(*UCP)[[:alpha:]]"}},
        doc=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": "café"},
            {"_id": 3, "a": "123"},
        ],
        expected=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": "café"}],
        msg="$regex (*UCP)[:alpha:] should match all Unicode alphabetic",
    ),
]

DIGIT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="digit_d_ascii_only",
        filter={"a": {"$regex": "^\\d+$"}},
        doc=[
            {"_id": 1, "a": "123"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "\u0661\u0662\u0663"},
        ],
        expected=[{"_id": 1, "a": "123"}],
        msg="$regex \\d should match ASCII digits only by default",
    ),
    QueryTestCase(
        id="digit_d_ucp",
        filter={"a": {"$regex": "(*UCP)^\\d+$"}},
        doc=[
            {"_id": 1, "a": "123"},
            {"_id": 2, "a": "abc"},
            {"_id": 3, "a": "\u0661\u0662\u0663"},
        ],
        expected=[{"_id": 1, "a": "123"}, {"_id": 3, "a": "\u0661\u0662\u0663"}],
        msg="$regex (*UCP)\\d should match all Unicode digit characters",
    ),
]

EMOJI_AND_COMBINING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="emoji_match",
        filter={"a": {"$regex": "😀"}},
        doc=[{"_id": 1, "a": "hello 😀"}, {"_id": 2, "a": "hello"}],
        expected=[{"_id": 1, "a": "hello 😀"}],
        msg="$regex should match emoji characters",
    ),
    QueryTestCase(
        id="combining_character_match",
        filter={"a": {"$regex": "e\u0301"}},
        doc=[{"_id": 1, "a": "e\u0301"}, {"_id": 2, "a": "e"}],
        expected=[{"_id": 1, "a": "e\u0301"}],
        msg="$regex should match combining characters (e + combining accent)",
    ),
]

NORMALIZATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nfc_does_not_match_nfd",
        filter={"a": {"$regex": "caf\u00e9"}},
        doc=[{"_id": 1, "a": "cafe\u0301"}, {"_id": 2, "a": "caf\u00e9"}],
        expected=[{"_id": 2, "a": "caf\u00e9"}],
        msg="$regex with precomposed é should not match decomposed "
        "e+combining accent (no normalization)",
    ),
    QueryTestCase(
        id="nfd_does_not_match_nfc",
        filter={"a": {"$regex": "cafe\u0301"}},
        doc=[{"_id": 1, "a": "caf\u00e9"}, {"_id": 2, "a": "cafe\u0301"}],
        expected=[{"_id": 2, "a": "cafe\u0301"}],
        msg="$regex with decomposed e+accent should not match precomposed é (no normalization)",
    ),
]

NEGATED_PROPERTY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negated_unicode_property_P_L",
        filter={"a": {"$regex": "^\\P{L}+$"}},
        doc=[
            {"_id": 1, "a": "123!@#"},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": "12ab"},
        ],
        expected=[{"_id": 1, "a": "123!@#"}],
        msg="$regex \\P{L} should match only non-letter characters",
    ),
]

CASE_FOLDING_EDGE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="turkish_dotted_I_case_insensitive",
        filter={"a": {"$regex": "istanbul", "$options": "i"}},
        doc=[
            {"_id": 1, "a": "Istanbul"},
            {"_id": 2, "a": "\u0130stanbul"},
        ],
        expected=[{"_id": 1, "a": "Istanbul"}],
        msg="$regex /istanbul/i should match Istanbul but not İstanbul (dotted İ is distinct)",
    ),
    QueryTestCase(
        id="german_eszett_case_insensitive",
        filter={"a": {"$regex": "stra\u00dfe", "$options": "i"}},
        doc=[
            {"_id": 1, "a": "Stra\u00dfe"},
            {"_id": 2, "a": "STRASSE"},
        ],
        expected=[{"_id": 1, "a": "Stra\u00dfe"}],
        msg="$regex /straße/i should match Straße but not STRASSE (no full case folding)",
    ),
]

ALL_TESTS = (
    UNICODE_MATCHING_TESTS
    + UCP_TESTS
    + UNICODE_PROPERTY_TESTS
    + UTF_PREFIX_TESTS
    + POSIX_CLASS_TESTS
    + DIGIT_TESTS
    + EMOJI_AND_COMBINING_TESTS
    + NORMALIZATION_TESTS
    + NEGATED_PROPERTY_TESTS
    + CASE_FOLDING_EDGE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_regex_unicode(collection, test):
    """Parametrized test for $regex Unicode and encoding behavior."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
