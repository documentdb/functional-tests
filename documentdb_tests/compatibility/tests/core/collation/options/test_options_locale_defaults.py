"""Tests for locale-specific default behavior and simple locale overrides."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Simple Locale Overrides All Options]: locale "simple" causes all
# other collation options to be accepted but have no observable effect because
# binary comparison is always used.
COLLATION_SIMPLE_LOCALE_OVERRIDES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "simple_casefirst_upper_strength1_accepted",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "A"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "simple",
                "strength": 1,
                "caseFirst": "upper",
            },
        },
        # Binary sort: A (65) < a (97).
        expected=[{"_id": 2, "x": "A"}, {"_id": 1, "x": "a"}],
        msg="simple locale should accept caseFirst upper with strength 1 without error",
    ),
    CommandTestCase(
        "simple_backwards_true_strength1_accepted",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "A"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "simple",
                "strength": 1,
                "backwards": True,
            },
        },
        # Binary sort: A (65) < a (97).
        expected=[{"_id": 2, "x": "A"}, {"_id": 1, "x": "a"}],
        msg="simple locale should accept backwards true with strength 1 without error",
    ),
    CommandTestCase(
        "simple_numeric_ordering_no_effect",
        docs=[{"_id": 1, "x": "10"}, {"_id": 2, "x": "2"}, {"_id": 3, "x": "1"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "simple", "numericOrdering": True},
        },
        # Binary/lexicographic sort: "1" < "10" < "2".
        expected=[
            {"_id": 3, "x": "1"},
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
        ],
        msg="simple locale should ignore numericOrdering and use binary comparison",
    ),
    CommandTestCase(
        "simple_strength1_binary_comparison",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "A"}, {"_id": 3, "x": "B"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "simple", "strength": 1},
        },
        # Binary sort: A (65) < B (66) < a (97).
        expected=[
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "B"},
            {"_id": 1, "x": "a"},
        ],
        msg="simple locale with strength 1 should still use binary comparison",
    ),
]

# Property [Locale-Specific Default Differences]: certain locales have
# non-standard default behaviors that differ from the general collation rules.
COLLATION_LOCALE_SPECIFIC_DEFAULTS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "locale_th_shifted_default_match",
        docs=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {"locale": "th", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        msg="th locale should default to alternate:shifted making punctuation/whitespace ignorable",
    ),
    CommandTestCase(
        "locale_zh_secondary_weight_ordering",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "\u00e0"},
            {"_id": 3, "x": "\u00e1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "zh", "strength": 2},
        },
        expected=[
            {"_id": 3, "x": "\u00e1"},
            {"_id": 2, "x": "\u00e0"},
            {"_id": 1, "x": "a"},
        ],
        msg="zh locale should sort accented Latin characters before unaccented at secondary level",
    ),
    CommandTestCase(
        "locale_en_us_posix_strength1_not_case_insensitive",
        docs=[
            {"_id": 1, "x": "abc"},
            {"_id": 2, "x": "ABC"},
            {"_id": 3, "x": "Abc"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "abc"}}],
            "cursor": {},
            "collation": {"locale": "en_US_POSIX", "strength": 1},
        },
        expected=[{"_id": 1, "x": "abc"}],
        msg="en_US_POSIX strength 1 should NOT enable case-insensitive matching",
    ),
    CommandTestCase(
        "locale_en_us_posix_enforces_casefirst_constraint",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en_US_POSIX", "caseFirst": "upper", "strength": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="en_US_POSIX should enforce caseFirst constraint unlike simple locale",
    ),
    CommandTestCase(
        "locale_de_eszett_equals_ss_strength1",
        docs=[
            {"_id": 1, "x": "stra\u00dfe"},
            {"_id": 2, "x": "strasse"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "strasse"}}],
            "cursor": {},
            "collation": {"locale": "de", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "stra\u00dfe"},
            {"_id": 2, "x": "strasse"},
        ],
        msg="de locale strength 1 should treat \u00df as equivalent to ss",
    ),
    CommandTestCase(
        "locale_de_eszett_distinct_strength2",
        docs=[
            {"_id": 1, "x": "stra\u00dfe"},
            {"_id": 2, "x": "strasse"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "strasse"}}],
            "cursor": {},
            "collation": {"locale": "de", "strength": 2},
        },
        expected=[{"_id": 2, "x": "strasse"}],
        msg="de locale strength 2 should distinguish \u00df from ss",
    ),
    CommandTestCase(
        "locale_tr_i_maps_to_dotted_I",
        docs=[
            {"_id": 1, "x": "i"},
            {"_id": 2, "x": "I"},
            {"_id": 3, "x": "\u0130"},
            {"_id": 4, "x": "\u0131"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "i"}}],
            "cursor": {},
            # Turkish: i <-> \u0130 (dotted I).
            "collation": {"locale": "tr", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "i"},
            {"_id": 3, "x": "\u0130"},
        ],
        msg="tr locale should fold i to \u0130 (not I) at strength 1",
    ),
    CommandTestCase(
        "locale_tr_I_maps_to_dotless_i",
        docs=[
            {"_id": 1, "x": "i"},
            {"_id": 2, "x": "I"},
            {"_id": 3, "x": "\u0130"},
            {"_id": 4, "x": "\u0131"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "I"}}],
            "cursor": {},
            # Turkish: I <-> \u0131 (dotless i).
            "collation": {"locale": "tr", "strength": 1},
        },
        expected=[
            {"_id": 2, "x": "I"},
            {"_id": 4, "x": "\u0131"},
        ],
        msg="tr locale should fold I to \u0131 (not i) at strength 1",
    ),
]

COLLATION_LOCALE_DEFAULTS_TESTS: list[CommandTestCase] = (
    COLLATION_SIMPLE_LOCALE_OVERRIDES_TESTS + COLLATION_LOCALE_SPECIFIC_DEFAULTS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_LOCALE_DEFAULTS_TESTS))
def test_collation_locale_defaults(database_client, collection, test):
    """Test locale-specific default behavior and simple locale overrides."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
