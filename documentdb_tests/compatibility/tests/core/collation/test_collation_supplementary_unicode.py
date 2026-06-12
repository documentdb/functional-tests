"""Tests for collation behavior with supplementary Unicode characters (outside BMP)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Supplementary Character Matching]: collation correctly handles
# characters outside the Basic Multilingual Plane (U+10000+) for equality
# and comparison operations.
COLLATION_SUPPLEMENTARY_MATCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "emoji_equality",
        docs=[
            # U+1F34E red apple, U+1F34F green apple, U+1F34A tangerine.
            {"_id": 1, "x": "\U0001f34e"},
            {"_id": 2, "x": "\U0001f34f"},
            {"_id": 3, "x": "\U0001f34a"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "\U0001f34e"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "\U0001f34e"}],
        msg="find should match supplementary characters exactly under collation",
    ),
    CommandTestCase(
        "emoji_ne",
        docs=[
            {"_id": 1, "x": "\U0001f34e"},
            {"_id": 2, "x": "\U0001f34f"},
            {"_id": 3, "x": "\U0001f34a"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$ne": "\U0001f34e"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": 2, "x": "\U0001f34f"},
            {"_id": 3, "x": "\U0001f34a"},
        ],
        msg="find $ne should correctly exclude supplementary characters under collation",
    ),
    CommandTestCase(
        "musical_symbols_equality",
        docs=[
            # U+1D11E musical symbol G clef, U+1D122 musical symbol F clef.
            {"_id": 1, "x": "\U0001d11e"},
            {"_id": 2, "x": "\U0001d122"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "\U0001d11e"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "\U0001d11e"}],
        msg="find should match supplementary musical symbols under collation",
    ),
]

# Property [Supplementary Character Sort Ordering]: collation produces a
# consistent sort order for supplementary characters.
COLLATION_SUPPLEMENTARY_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "emoji_sort_consistent",
        docs=[
            {"_id": 1, "x": "\U0001f34e"},
            {"_id": 2, "x": "\U0001f34a"},
            {"_id": 3, "x": "apple"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": 2, "x": "\U0001f34a"},
            {"_id": 1, "x": "\U0001f34e"},
            {"_id": 3, "x": "apple"},
        ],
        msg="supplementary characters should sort before Latin letters under collation",
    ),
    CommandTestCase(
        "supplementary_mixed_with_bmp_sort",
        docs=[
            {"_id": 1, "x": "z"},
            {"_id": 2, "x": "\U00010000"},
            {"_id": 3, "x": "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": 3, "x": "a"},
            {"_id": 1, "x": "z"},
            {"_id": 2, "x": "\U00010000"},
        ],
        msg="supplementary U+10000 should sort after Latin letters under collation",
    ),
]

# Property [Supplementary Character Deduplication]: collation correctly
# deduplicates supplementary characters in $group and distinct.
COLLATION_SUPPLEMENTARY_DEDUP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "distinct_supplementary",
        docs=[
            {"_id": 1, "x": "\U0001f34e"},
            {"_id": 2, "x": "\U0001f34e"},
            {"_id": 3, "x": "\U0001f34a"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"values": ["\U0001f34a", "\U0001f34e"], "ok": 1.0},
        msg="distinct should correctly deduplicate supplementary characters",
    ),
    CommandTestCase(
        "group_supplementary",
        docs=[
            {"_id": 1, "x": "\U0001f34e", "v": 1},
            {"_id": 2, "x": "\U0001f34e", "v": 2},
            {"_id": 3, "x": "\U0001f34a", "v": 3},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": "$x", "total": {"$sum": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": "\U0001f34a", "total": 3},
            {"_id": "\U0001f34e", "total": 3},
        ],
        msg="$group should correctly group supplementary characters under collation",
    ),
]

# Property [Supplementary Characters with String Prefix]: strings that share a
# BMP prefix but differ in a supplementary character suffix are correctly
# distinguished.
COLLATION_SUPPLEMENTARY_PREFIX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "prefix_with_different_supplementary_suffix",
        docs=[
            {"_id": 1, "x": "fruit\U0001f34e"},
            {"_id": 2, "x": "fruit\U0001f34a"},
            {"_id": 3, "x": "fruit"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "fruit\U0001f34e"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "fruit\U0001f34e"}],
        msg="find should distinguish strings differing only in supplementary suffix",
    ),
]

COLLATION_SUPPLEMENTARY_TESTS: list[CommandTestCase] = (
    COLLATION_SUPPLEMENTARY_MATCH_TESTS
    + COLLATION_SUPPLEMENTARY_SORT_TESTS
    + COLLATION_SUPPLEMENTARY_DEDUP_TESTS
    + COLLATION_SUPPLEMENTARY_PREFIX_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_SUPPLEMENTARY_TESTS))
def test_collation_supplementary_unicode(database_client, collection, test):
    """Test collation behavior with supplementary Unicode characters."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(test.build_expected(ctx), list),
    )
