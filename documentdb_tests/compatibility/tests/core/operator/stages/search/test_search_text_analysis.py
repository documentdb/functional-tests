"""Tests for $search default analyzer tokenization and case folding."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)

pytestmark = pytest.mark.requires(search=True)


# Property [ASCII Case Folding]: ASCII letter case is folded during analysis, so a
# query token matches a stored token of any letter case.
SEARCH_ASCII_CASE_FOLD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "case_fold_upper",
        pipeline=[
            {"$search": {"text": {"query": "QUICK", "path": "title"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should match an all-uppercase query against a stored lowercase token",
    ),
    StageTestCase(
        "case_fold_mixed",
        pipeline=[
            {"$search": {"text": {"query": "QuIcK", "path": "title"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should match a mixed-case query against a stored lowercase token",
    ),
]

# Property [Single-Character Token]: the analyzer preserves a single-character
# token so a one-character query matches its stored one-character form.
SEARCH_SINGLE_CHAR_TOKEN_TESTS: list[StageTestCase] = [
    StageTestCase(
        "single_char_token",
        pipeline=[{"$search": {"text": {"query": "x", "path": "title"}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 6)]},
        msg="$search should match a single-character query against a stored single-character token",
    ),
]

# Property [Non-ASCII Case Folding]: simple 1:1 case folding is applied to
# non-ASCII cased scripts, so a query matches a stored token of the opposite case.
SEARCH_NON_ASCII_CASE_FOLD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fold_greek",
        pipeline=[
            {"$search": {"text": {"query": "ΣΙΓΜΑ", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 7)]},
        msg="$search should fold uppercase Greek to match a stored lowercase Greek token",
    ),
    StageTestCase(
        "fold_cyrillic",
        pipeline=[
            {"$search": {"text": {"query": "ДЕНЬ", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 8)]},
        msg="$search should fold uppercase Cyrillic to match a stored lowercase Cyrillic token",
    ),
    StageTestCase(
        "fold_supplementary_plane",
        # Deseret capital long I (U+10400) folds to small letter long I (U+10428).
        pipeline=[
            {"$search": {"text": {"query": "\U00010400", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 9)]},
        msg="$search should fold an uppercase supplementary-plane letter to match its "
        "stored lowercase form",
    ),
]

# Property [No-Match Tokenization]: a query that produces no token matching a
# stored token returns no documents without error.
SEARCH_NO_MATCH_TOKEN_TESTS: list[StageTestCase] = [
    StageTestCase(
        "no_match_whitespace",
        pipeline=[
            {"$search": {"text": {"query": "   ", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for a whitespace-only query",
    ),
    StageTestCase(
        "no_match_punctuation",
        pipeline=[
            {"$search": {"text": {"query": "!!!", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for a punctuation-only query",
    ),
    StageTestCase(
        "no_match_null_byte",
        pipeline=[
            {"$search": {"text": {"query": "\x00", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for a lone null-byte query",
    ),
    StageTestCase(
        "no_match_cjk",
        pipeline=[
            {"$search": {"text": {"query": "日本語", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for a CJK run with no stored token",
    ),
    StageTestCase(
        "no_match_emoji",
        pipeline=[
            {"$search": {"text": {"query": "😀😀", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for an emoji run with no stored token",
    ),
    StageTestCase(
        "no_match_accented",
        pipeline=[
            {"$search": {"text": {"query": "çàü", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for an accented run with no stored token",
    ),
    StageTestCase(
        "no_match_zwsp",
        # Zero-width space (U+200B) carries no token content.
        pipeline=[
            {"$search": {"text": {"query": "\u200b", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for a zero-width-space-only query",
    ),
    StageTestCase(
        "no_match_digits",
        pipeline=[
            {"$search": {"text": {"query": "12345", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should match nothing for a pure-digit query with no stored digit token",
    ),
]

# Property [No Diacritic/NFC/NFD/Ligature/Locale Normalization]: the default
# analyzer leaves canonically- or compatibility-equivalent forms as distinct
# tokens, so a query matches only its own stored form and never an equivalent one.
SEARCH_NO_NORMALIZATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "norm_diacritic_plain",
        pipeline=[
            {"$search": {"text": {"query": "resume", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 10)]},
        msg="$search should match a plain-ASCII query only against its undecorated stored token",
    ),
    StageTestCase(
        "norm_diacritic_accented",
        pipeline=[
            {"$search": {"text": {"query": "r\u00e9sum\u00e9", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 5)]},
        msg="$search should match an accented query only against its accented stored token",
    ),
    StageTestCase(
        "norm_nfc_precomposed",
        pipeline=[
            {"$search": {"text": {"query": "caf\u00e9", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 11)]},
        msg="$search should match a precomposed query against its precomposed stored token",
    ),
    StageTestCase(
        "norm_nfd_combining",
        # "cafe" followed by combining acute accent (U+0301).
        pipeline=[
            {"$search": {"text": {"query": "cafe\u0301", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should not normalize a combining-form query to match a precomposed token",
    ),
    StageTestCase(
        "norm_ligature_stored",
        pipeline=[
            {"$search": {"text": {"query": "\ufb01le", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 12)]},
        msg="$search should match a ligature query against its ligature stored token",
    ),
    StageTestCase(
        "norm_ligature_decomposed",
        pipeline=[
            {"$search": {"text": {"query": "file", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should not decompose a ligature token to match a plain-letter query",
    ),
    StageTestCase(
        "norm_german_stored",
        pipeline=[
            {"$search": {"text": {"query": "stra\u00dfe", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 13)]},
        msg="$search should match an eszett query against its eszett stored token",
    ),
    StageTestCase(
        "norm_german_lower_expansion",
        pipeline=[
            {"$search": {"text": {"query": "strasse", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should not expand eszett to ss to match a lowercase query",
    ),
    StageTestCase(
        "norm_german_upper_expansion",
        pipeline=[
            {"$search": {"text": {"query": "STRASSE", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should not expand eszett to ss to match an uppercase query",
    ),
    StageTestCase(
        "norm_turkish_stored",
        pipeline=[
            {"$search": {"text": {"query": "\u0131rmak", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 14)]},
        msg="$search should match a dotless-i query against its dotless-i stored token",
    ),
    StageTestCase(
        "norm_turkish_upper",
        pipeline=[
            {"$search": {"text": {"query": "IRMAK", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should not locale-fold an uppercase I to match a dotless-i token",
    ),
    StageTestCase(
        "norm_turkish_ascii_lower",
        pipeline=[
            {"$search": {"text": {"query": "irmak", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should treat ASCII dotted i as distinct from a dotless-i token",
    ),
]

# Property [ASCII Fold Range Edges]: ASCII case folding applies precisely at the
# A-Z range boundaries, with no off-by-one at the first or last letter of the range.
SEARCH_ASCII_EDGE_FOLD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "edge_fold_first_letter",
        pipeline=[{"$search": {"text": {"query": "A", "path": "title"}}}],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 3), Contains("_id", 15)]},
        msg="$search should fold an uppercase A at the range start to match a stored lowercase a",
    ),
    StageTestCase(
        "edge_fold_last_letter",
        pipeline=[{"$search": {"text": {"query": "Z", "path": "title"}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 15)]},
        msg="$search should fold an uppercase Z at the range end to match a stored lowercase z",
    ),
]

# Property [Whitespace and Control Token Boundaries]: Unicode whitespace
# categories, control characters, and backslash each act as a token boundary
# identically to ASCII space, splitting a query into separate tokens, while a
# backslash-only query yields no token and matches nothing.
SEARCH_TOKEN_BOUNDARY_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"boundary_{name}",
            pipeline=[
                {"$search": {"text": {"query": f"word{sep}joined", "path": "title"}}},
            ],
            expected={"cursor.firstBatch": [Len(1), Contains("_id", 16)]},
            msg=f"$search should treat {desc} as a token boundary, matching the "
            "two-token document and not the one-token document",
        )
        for name, sep, desc in [
            ("nbsp", "\u00a0", "a no-break space (U+00A0)"),
            ("en_space", "\u2000", "an en space (U+2000)"),
            ("tab", "\t", "a tab"),
            ("newline", "\n", "a newline"),
            ("control_0001", "\u0001", "a control character (U+0001)"),
            ("control_001f", "\u001f", "a control character (U+001F)"),
            ("backslash", "\\", "a backslash"),
        ]
    ],
    StageTestCase(
        "boundary_backslash_only",
        pipeline=[
            {"$search": {"text": {"query": "\\", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should produce no token for a backslash-only query and match nothing",
    ),
]

# Property [Zero-Width Token Boundaries]: a zero-width space splits a token while
# an embedded BOM or ZWJ is retained inside the token (matching neither the split
# nor the joined form), and a leading BOM is stripped so the remaining token still
# matches.
SEARCH_ZERO_WIDTH_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "zwsp_boundary",
        # Zero-width space (U+200B) acts as a token boundary.
        pipeline=[
            {"$search": {"text": {"query": "word\u200bjoined", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 16)]},
        msg="$search should treat a zero-width space as a token boundary, matching the "
        "two-token document and not the one-token document",
    ),
    StageTestCase(
        "bom_embedded_retained",
        # BOM (U+FEFF) embedded mid-token is retained inside the token.
        pipeline=[
            {"$search": {"text": {"query": "word\ufeffjoined", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should retain an embedded BOM inside the token, matching neither the "
        "split nor the joined form",
    ),
    StageTestCase(
        "zwj_embedded_retained",
        # ZWJ (U+200D) embedded mid-token is retained inside the token.
        pipeline=[
            {"$search": {"text": {"query": "word\u200djoined", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should retain an embedded ZWJ inside the token, matching neither the "
        "split nor the joined form",
    ),
    StageTestCase(
        "bom_leading_stripped",
        # A leading BOM (U+FEFF) is stripped, leaving the joined token intact.
        pipeline=[
            {"$search": {"text": {"query": "\ufeffwordjoined", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 17)]},
        msg="$search should strip a leading BOM so the remaining one-token form still matches",
    ),
]

SEARCH_TEXT_ANALYSIS_TESTS = (
    SEARCH_ASCII_CASE_FOLD_TESTS
    + SEARCH_SINGLE_CHAR_TOKEN_TESTS
    + SEARCH_NON_ASCII_CASE_FOLD_TESTS
    + SEARCH_NO_MATCH_TOKEN_TESTS
    + SEARCH_NO_NORMALIZATION_TESTS
    + SEARCH_ASCII_EDGE_FOLD_TESTS
    + SEARCH_TOKEN_BOUNDARY_TESTS
    + SEARCH_ZERO_WIDTH_BOUNDARY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_TEXT_ANALYSIS_TESTS))
def test_search_text_analysis_cases(indexed_collection, test_case: StageTestCase):
    """Test $search default analyzer tokenization and case folding."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )
