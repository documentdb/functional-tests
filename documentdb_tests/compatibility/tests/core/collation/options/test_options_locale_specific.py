"""Tests for locale-specific collation behaviors not covered by other locale tests."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Swedish Sort Order]: the Swedish locale sorts å, ä, ö after z,
# unlike English which sorts them near their base characters.
COLLATION_SWEDISH_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sv_a_ring_after_z",
        docs=[
            {"_id": 1, "x": "z"},
            {"_id": 2, "x": "\u00e5"},
            {"_id": 3, "x": "\u00e4"},
            {"_id": 4, "x": "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "sv", "strength": 3},
        },
        expected=[
            {"_id": 4, "x": "a"},
            {"_id": 1, "x": "z"},
            {"_id": 2, "x": "\u00e5"},
            {"_id": 3, "x": "\u00e4"},
        ],
        msg="sv locale should sort \u00e5 and \u00e4 after z",
    ),
    CommandTestCase(
        "en_a_ring_before_z",
        docs=[
            {"_id": 1, "x": "z"},
            {"_id": 2, "x": "\u00e5"},
            {"_id": 3, "x": "\u00e4"},
            {"_id": 4, "x": "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": 4, "x": "a"},
            {"_id": 2, "x": "\u00e5"},
            {"_id": 3, "x": "\u00e4"},
            {"_id": 1, "x": "z"},
        ],
        msg="en locale should sort \u00e5 and \u00e4 before z",
    ),
    CommandTestCase(
        "sv_match_a_ring_distinct_from_a",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "\u00e5"},
            {"_id": 3, "x": "\u00e4"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "sv", "strength": 1},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="sv locale strength 1 should distinguish a from \u00e5 and \u00e4",
    ),
]

# Property [Japanese Hiragana/Katakana Equivalence]: Hiragana and Katakana
# forms of the same character are treated as equivalent at strengths 1-3;
# they are distinguished at strength 4 (quaternary).
COLLATION_JAPANESE_KANA_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ja_strength1_hiragana_equals_katakana_match",
        docs=[
            # U+3042 hiragana a, U+30A2 katakana a.
            {"_id": 1, "x": "\u3042"},
            {"_id": 2, "x": "\u30a2"},
            {"_id": 3, "x": "\u3044"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\u3042"}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "ja", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "\u3042"},
            {"_id": 2, "x": "\u30a2"},
        ],
        msg="ja locale strength 1 should treat hiragana and katakana as equivalent",
    ),
    CommandTestCase(
        "ja_strength3_hiragana_equals_katakana",
        docs=[
            {"_id": 1, "x": "\u3042"},
            {"_id": 2, "x": "\u30a2"},
            {"_id": 3, "x": "\u3044"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\u3042"}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "ja", "strength": 3},
        },
        expected=[
            {"_id": 1, "x": "\u3042"},
            {"_id": 2, "x": "\u30a2"},
        ],
        msg="ja locale strength 3 should still treat hiragana and katakana as equivalent",
    ),
    CommandTestCase(
        "ja_strength4_hiragana_distinct_from_katakana",
        docs=[
            {"_id": 1, "x": "\u3042"},
            {"_id": 2, "x": "\u30a2"},
            {"_id": 3, "x": "\u3044"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\u3042"}}],
            "cursor": {},
            "collation": {"locale": "ja", "strength": 4},
        },
        expected=[{"_id": 1, "x": "\u3042"}],
        msg="ja locale strength 4 should distinguish hiragana from katakana",
    ),
    CommandTestCase(
        "ja_strength1_multichar_kana_match",
        docs=[
            # Hiragana "ka" + "na" vs Katakana "ka" + "na".
            {"_id": 1, "x": "\u304b\u306a"},
            {"_id": 2, "x": "\u30ab\u30ca"},
            {"_id": 3, "x": "\u305f"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\u304b\u306a"}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "ja", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "\u304b\u306a"},
            {"_id": 2, "x": "\u30ab\u30ca"},
        ],
        msg="ja locale strength 1 should treat multi-character hiragana/katakana as equivalent",
    ),
]

# Property [Korean Jamo vs Precomposed Syllables]: Korean precomposed syllables
# and their Jamo decompositions are treated as equivalent under normalization
# or at appropriate strength levels.
COLLATION_KOREAN_JAMO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ko_precomposed_equals_jamo_sort",
        docs=[
            # U+AC00 = precomposed "ga", U+1100 U+1161 = Jamo "g" + "a".
            {"_id": 1, "x": "\uac00"},
            {"_id": 2, "x": "\u1100\u1161"},
            {"_id": 3, "x": "\uac01"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\uac00"}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "ko", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "\uac00"},
            {"_id": 2, "x": "\u1100\u1161"},
        ],
        msg="ko locale should treat precomposed syllable and Jamo decomposition as equivalent",
    ),
    CommandTestCase(
        "ko_precomposed_sort_order",
        docs=[
            {"_id": 1, "x": "\ub098"},
            {"_id": 2, "x": "\uac00"},
            {"_id": 3, "x": "\ub2e4"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "ko", "strength": 1},
        },
        expected=[
            {"_id": 2, "x": "\uac00"},
            {"_id": 1, "x": "\ub098"},
            {"_id": 3, "x": "\ub2e4"},
        ],
        msg="ko locale should sort precomposed syllables in Korean alphabetical order",
    ),
]

COLLATION_LOCALE_SPECIFIC_TESTS: list[CommandTestCase] = (
    COLLATION_SWEDISH_SORT_TESTS + COLLATION_JAPANESE_KANA_TESTS + COLLATION_KOREAN_JAMO_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_LOCALE_SPECIFIC_TESTS))
def test_collation_locale_specific(database_client, collection, test):
    """Test locale-specific collation behaviors."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
