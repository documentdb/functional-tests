"""Tests for numericOrdering behavior and null acceptance in collation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [numericOrdering Behavior]: numericOrdering:true compares contiguous
# digit substrings as numbers rather than lexicographically.
COLLATION_NUMERIC_ORDERING_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "numeric_ordering_true_sort",
        docs=[
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
            {"_id": 3, "x": "1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 3, "x": "1"},
            {"_id": 2, "x": "2"},
            {"_id": 1, "x": "10"},
        ],
        msg="numericOrdering:true should sort digit substrings numerically",
    ),
    CommandTestCase(
        "numeric_ordering_false_sort",
        docs=[
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
            {"_id": 3, "x": "1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": False},
        },
        expected=[
            {"_id": 3, "x": "1"},
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
        ],
        msg="numericOrdering:false should sort digit substrings lexicographically",
    ),
    CommandTestCase(
        "numeric_ordering_separator_dot",
        docs=[
            {"_id": 1, "x": "1.10"},
            {"_id": 2, "x": "1.2"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "1.2"},
            {"_id": 1, "x": "1.10"},
        ],
        msg="dot should split digit groups so 1.2 < 1.10 numerically",
    ),
    CommandTestCase(
        "numeric_ordering_separator_hyphen",
        docs=[
            {"_id": 1, "x": "1-10"},
            {"_id": 2, "x": "1-2"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "1-2"},
            {"_id": 1, "x": "1-10"},
        ],
        msg="hyphen should split digit groups so 1-2 < 1-10 numerically",
    ),
    CommandTestCase(
        "numeric_ordering_separator_comma",
        docs=[
            {"_id": 1, "x": "1,10"},
            {"_id": 2, "x": "1,2"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "1,2"},
            {"_id": 1, "x": "1,10"},
        ],
        msg="comma should split digit groups so 1,2 < 1,10 numerically",
    ),
    CommandTestCase(
        "numeric_ordering_separator_space",
        docs=[
            {"_id": 1, "x": "1 10"},
            {"_id": 2, "x": "1 2"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "1 2"},
            {"_id": 1, "x": "1 10"},
        ],
        msg="space should split digit groups so 1 2 < 1 10 numerically",
    ),
    CommandTestCase(
        "numeric_ordering_separator_e",
        docs=[
            {"_id": 1, "x": "1e10"},
            {"_id": 2, "x": "1e2"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "1e2"},
            {"_id": 1, "x": "1e10"},
        ],
        msg="letter e should split digit groups and not be treated as exponent",
    ),
    CommandTestCase(
        "numeric_ordering_leading_zeros_equal_strength4",
        docs=[
            {"_id": 1, "x": "007"},
            {"_id": 2, "x": "7"},
            {"_id": 3, "x": "07"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "7"}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True, "strength": 4},
        },
        expected=[
            {"_id": 1, "x": "007"},
            {"_id": 2, "x": "7"},
            {"_id": 3, "x": "07"},
        ],
        msg="leading zeros should be numerically equal at strength 4",
    ),
    CommandTestCase(
        "numeric_ordering_leading_zeros_distinct_strength5",
        docs=[
            {"_id": 1, "x": "007"},
            {"_id": 2, "x": "7"},
            {"_id": 3, "x": "07"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "7"}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True, "strength": 5},
        },
        expected=[{"_id": 2, "x": "7"}],
        msg="leading zeros should be distinguished at strength 5",
    ),
    CommandTestCase(
        "numeric_ordering_leading_zeros_sort_strength5",
        docs=[
            {"_id": 1, "x": "7"},
            {"_id": 2, "x": "007"},
            {"_id": 3, "x": "07"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True, "strength": 5},
        },
        expected=[
            {"_id": 2, "x": "007"},
            {"_id": 3, "x": "07"},
            {"_id": 1, "x": "7"},
        ],
        msg="at strength 5 more leading zeros should sort earlier",
    ),
    CommandTestCase(
        "numeric_ordering_unicode_arabic_indic",
        docs=[
            {"_id": 1, "x": "\u0661\u0660"},
            {"_id": 2, "x": "\u0662"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "\u0662"},
            {"_id": 1, "x": "\u0661\u0660"},
        ],
        msg="Arabic-Indic Nd digits should be compared numerically",
    ),
    CommandTestCase(
        "numeric_ordering_unicode_fullwidth",
        docs=[
            {"_id": 1, "x": "\uff11\uff10"},
            {"_id": 2, "x": "\uff12"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "\uff12"},
            {"_id": 1, "x": "\uff11\uff10"},
        ],
        msg="Fullwidth Nd digits should be compared numerically",
    ),
    CommandTestCase(
        "numeric_ordering_unicode_devanagari",
        docs=[
            {"_id": 1, "x": "\u0967\u0966"},
            {"_id": 2, "x": "\u0968"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "\u0968"},
            {"_id": 1, "x": "\u0967\u0966"},
        ],
        msg="Devanagari Nd digits should be compared numerically",
    ),
    CommandTestCase(
        "numeric_ordering_unicode_thai",
        docs=[
            {"_id": 1, "x": "\u0e51\u0e50"},
            {"_id": 2, "x": "\u0e52"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "\u0e52"},
            {"_id": 1, "x": "\u0e51\u0e50"},
        ],
        msg="Thai Nd digits should be compared numerically",
    ),
    CommandTestCase(
        "numeric_ordering_mixed_script_merged",
        docs=[
            {"_id": 1, "x": "1\u0662"},
            {"_id": 2, "x": "5"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "5"},
            {"_id": 1, "x": "1\u0662"},
        ],
        msg="mixed-script adjacent Nd digits are merged into one numeric group",
    ),
    CommandTestCase(
        "numeric_ordering_254_boundary_split",
        docs=[
            {"_id": 1, "x": "9" * 254},
            {"_id": 2, "x": "1" * 255},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "1" * 255},
            {"_id": 1, "x": "9" * 254},
        ],
        msg="255-digit number should sort before 254-digit number due to 254-char split",
    ),
    CommandTestCase(
        "numeric_ordering_254_no_split",
        docs=[
            {"_id": 1, "x": "9" * 253},
            {"_id": 2, "x": "1" * 254},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 1, "x": "9" * 253},
            {"_id": 2, "x": "1" * 254},
        ],
        msg="254-digit number should sort correctly without split (more digits = larger)",
    ),
    CommandTestCase(
        "numeric_ordering_non_nd_superscript",
        docs=[
            {"_id": 1, "x": "a\u00b3"},
            {"_id": 2, "x": "a\u00b9\u00b2"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "a\u00b9\u00b2"},
            {"_id": 1, "x": "a\u00b3"},
        ],
        msg="superscript digits should not be treated as numeric digits",
    ),
    CommandTestCase(
        "numeric_ordering_non_nd_circled",
        docs=[
            {"_id": 1, "x": "a\u2462"},
            {"_id": 2, "x": "a\u2460\u2461"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "a\u2460\u2461"},
            {"_id": 1, "x": "a\u2462"},
        ],
        msg="circled digits should not be treated as numeric digits",
    ),
    CommandTestCase(
        "numeric_ordering_non_nd_roman",
        docs=[
            {"_id": 1, "x": "a\u2161"},
            {"_id": 2, "x": "a3"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 2, "x": "a3"},
            {"_id": 1, "x": "a\u2161"},
        ],
        msg="Roman numeral characters should not be treated as numeric digits",
    ),
]

# Property [numericOrdering Null Acceptance]: null for numericOrdering is
# treated as omitted, using the default value of false.
COLLATION_NUMERIC_ORDERING_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "numeric_ordering_null_uses_default_false",
        docs=[
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
            {"_id": 3, "x": "1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": None},
        },
        expected=[
            {"_id": 3, "x": "1"},
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
        ],
        msg="aggregate should treat null numericOrdering as omitted (default false, lexicographic)",
    ),
]

COLLATION_NUMERIC_ORDERING_TESTS: list[CommandTestCase] = (
    COLLATION_NUMERIC_ORDERING_BEHAVIOR_TESTS + COLLATION_NUMERIC_ORDERING_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_NUMERIC_ORDERING_TESTS))
def test_collation_numeric_ordering(database_client, collection, test):
    """Test numericOrdering collation option behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
