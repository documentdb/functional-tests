"""Tests for strength field behavior in collation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Strength in $sort]: strength 1 treats all case and accent variants
# as equivalent (stable sort preserves insertion order), strength 2 distinguishes
# accents but not case, strength 3 distinguishes all, strength 4 additionally
# distinguishes punctuation when alternate is shifted, and strength 5
# distinguishes leading zeros in numeric ordering.
COLLATION_STRENGTH_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_strength1_equivalent_variants",
        docs=[
            {"_id": 1, "x": "b"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 2, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
            {"_id": 1, "x": "b"},
        ],
        msg="strength 1 sort should treat case and accent variants as equivalent",
    ),
    CommandTestCase(
        "sort_strength2_accent_distinct_case_equivalent",
        docs=[
            {"_id": 1, "x": "b"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 1, "x": "b"},
        ],
        msg="strength 2 sort should distinguish accents but treat case variants as equivalent",
    ),
    CommandTestCase(
        "sort_strength3_all_distinct",
        docs=[
            {"_id": 1, "x": "b"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
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
            {"_id": 3, "x": "A"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 1, "x": "b"},
        ],
        msg="strength 3 sort should produce distinct positions for case and accent variants",
    ),
    CommandTestCase(
        "sort_strength4_punctuation_with_shifted",
        docs=[
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a_b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 4, "alternate": "shifted"},
        },
        expected=[
            {"_id": 3, "x": "a_b"},
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
        ],
        msg="strength 4 with shifted should distinguish punctuation in sort order",
    ),
    CommandTestCase(
        "sort_strength3_shifted_punctuation_equivalent",
        docs=[
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a_b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3, "alternate": "shifted"},
        },
        expected=[
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a_b"},
        ],
        msg="strength 3 with shifted should treat punctuation as equivalent",
    ),
    CommandTestCase(
        "sort_strength5_zero_width_characters",
        docs=[
            {"_id": 1, "x": "a\u200bbc"},
            {"_id": 2, "x": "abc"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 5},
        },
        expected=[
            {"_id": 2, "x": "abc"},
            {"_id": 1, "x": "a\u200bbc"},
        ],
        msg="strength 5 should distinguish strings differing only by zero-width characters",
    ),
    CommandTestCase(
        "sort_strength4_zero_width_equivalent",
        docs=[
            {"_id": 1, "x": "a\u200bbc"},
            {"_id": 2, "x": "abc"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 4},
        },
        expected=[
            {"_id": 1, "x": "a\u200bbc"},
            {"_id": 2, "x": "abc"},
        ],
        msg="strength 4 should treat strings differing only by zero-width characters as equivalent",
    ),
]

# Property [Strength in $match]: strength 1 ignores diacritics and case,
# strength 2 ignores case but distinguishes diacritics, strength 3 (default)
# distinguishes both.
COLLATION_STRENGTH_MATCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "strength1_ignores_case_and_diacritics",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "caf\u00e9"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        msg="strength 1 should match all case and diacritic variants",
    ),
    CommandTestCase(
        "strength2_ignores_case_not_diacritics",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "cafe"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
        ],
        msg="strength 2 should match case variants but not diacritic variants",
    ),
    CommandTestCase(
        "strength2_diacritics_distinct",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "caf\u00e9"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        msg="strength 2 should match diacritic variants ignoring case",
    ),
    CommandTestCase(
        "strength3_distinguishes_case_and_diacritics",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "cafe"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "cafe"}],
        msg="strength 3 should match only exact case and diacritic",
    ),
    CommandTestCase(
        "strength_default_is_3",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "cafe"}}],
            "cursor": {},
            "collation": {"locale": "en"},
        },
        expected=[{"_id": 1, "x": "cafe"}],
        msg="default strength (omitted) should behave as strength 3",
    ),
]

COLLATION_STRENGTH_TESTS: list[CommandTestCase] = (
    COLLATION_STRENGTH_SORT_TESTS + COLLATION_STRENGTH_MATCH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_STRENGTH_TESTS))
def test_collation_strength(database_client, collection, test):
    """Test collation strength levels in sort and match."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
