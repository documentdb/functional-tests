"""Tests for collation with long strings and hint parameter interaction."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Long String Collation]: collation correctly compares strings of
# 10,000+ characters, including cases where the distinguishing difference
# appears near the end of the string.
COLLATION_LONG_STRING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "long_string_match_exact",
        docs=[
            {"_id": 1, "x": "a" * 10_000},
            {"_id": 2, "x": "a" * 9_999 + "b"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "a" * 10_000},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "a" * 10_000}],
        msg="collation should correctly match long strings without truncation",
    ),
    CommandTestCase(
        "long_string_case_difference_at_end",
        docs=[
            {"_id": 1, "x": "a" * 9_999 + "b"},
            {"_id": 2, "x": "a" * 9_999 + "B"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "a" * 9_999 + "b"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "a" * 9_999 + "b"},
            {"_id": 2, "x": "a" * 9_999 + "B"},
        ],
        msg="collation should detect case difference at end of long string",
    ),
    CommandTestCase(
        "long_string_sort_difference_at_end",
        docs=[
            {"_id": 1, "x": "a" * 9_999 + "c"},
            {"_id": 2, "x": "a" * 9_999 + "b"},
            {"_id": 3, "x": "a" * 9_999 + "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": 3, "x": "a" * 9_999 + "a"},
            {"_id": 2, "x": "a" * 9_999 + "b"},
            {"_id": 1, "x": "a" * 9_999 + "c"},
        ],
        msg="collation should correctly sort strings differing only at position 10000",
    ),
    CommandTestCase(
        "long_string_group_dedup",
        docs=[
            {"_id": 1, "x": "a" * 10_000 + "b", "v": 1},
            {"_id": 2, "x": "a" * 10_000 + "B", "v": 2},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": "$x", "total": {"$sum": "$v"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": "a" * 10_000 + "b", "total": 3}],
        msg="collation should correctly deduplicate long strings differing only in case at end",
    ),
]

# Property [Hint with Mismatched Collation]: when hint forces usage of a
# collated index but the query specifies a different collation, the server
# still returns correct results according to the query's collation.
COLLATION_HINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_collated_index_different_query_collation",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                name="x_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "hint": "x_ci",
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="hint with mismatched collation should return correct results per query collation",
    ),
    CommandTestCase(
        "hint_collated_index_matching_collation",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                name="x_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "hint": "x_ci",
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="hint with matching collation should return case-insensitive results",
    ),
    CommandTestCase(
        "hint_collated_index_no_query_collation",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                name="x_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "hint": "x_ci",
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="hint without query collation should use binary comparison not index collation",
    ),
]

COLLATION_LONG_STRING_AND_HINT_TESTS = COLLATION_LONG_STRING_TESTS + COLLATION_HINT_TESTS


@pytest.mark.parametrize("test", pytest_params(COLLATION_LONG_STRING_AND_HINT_TESTS))
def test_collation_long_strings_hint(database_client, collection, test):
    """Test collation with long strings and hint parameter."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
