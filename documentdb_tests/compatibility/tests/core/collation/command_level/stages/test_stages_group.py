"""Tests for collation effects on group key deduplication and accumulators."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Group Key Deduplication]: collation affects $group key comparisons
# so that collation-equal strings collapse into one group, with the
# first-encountered value used as the group key.
COLLATION_GROUP_KEY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "group_strength1_all_collapse",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
            {"_id": 5, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": "$x", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": "banana", "count": 1},
            {"_id": "cafe", "count": 4},
        ],
        msg="$group with strength 1 should collapse all case and accent variants",
    ),
    CommandTestCase(
        "group_strength2_accent_distinct_case_collapse",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
            {"_id": 5, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": "$x", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": "banana", "count": 1},
            {"_id": "cafe", "count": 2},
            {"_id": "caf\u00e9", "count": 2},
        ],
        msg="$group with strength 2 should collapse case but keep accents distinct",
    ),
    CommandTestCase(
        "group_strength3_all_distinct",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
            {"_id": 5, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": "$x", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": "banana", "count": 1},
            {"_id": "cafe", "count": 1},
            {"_id": "Cafe", "count": 1},
            {"_id": "caf\u00e9", "count": 1},
            {"_id": "CAF\u00c9", "count": 1},
        ],
        msg="$group with strength 3 should treat all variants as distinct groups",
    ),
    CommandTestCase(
        "group_first_encountered_key_asc",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": "$x", "count": {"$sum": 1}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": "apple", "count": 3}],
        msg="$group should use first-encountered value as group key (ascending sort)",
    ),
    CommandTestCase(
        "group_first_encountered_key_desc",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": -1}},
                {"$group": {"_id": "$x", "count": {"$sum": 1}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": "APPLE", "count": 3}],
        msg="$group should use first-encountered value as group key (descending sort)",
    ),
]

# Property [Group Accumulators Affected by Collation]: $addToSet, $min, and
# $max accumulators use collation for comparisons, while $first, $last, and
# $push are unaffected.
COLLATION_GROUP_ACCUMULATOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "group_addtoset_strength1_deduplicates",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": None, "unique_x": {"$addToSet": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "unique_x": ["apple"]}],
        msg="$addToSet with strength 1 should deduplicate all case variants",
    ),
    CommandTestCase(
        "group_addtoset_strength2_keeps_accents",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "CAF\u00c9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": None, "unique_x": {"$addToSet": "$x"}}},
                {"$project": {"unique_x": {"$sortArray": {"input": "$unique_x", "sortBy": 1}}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": None, "unique_x": ["cafe", "caf\u00e9"]}],
        msg="$addToSet with strength 2 should keep accent variants but collapse case variants",
    ),
    CommandTestCase(
        "group_min_uses_collation",
        docs=[
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
            {"_id": 3, "x": "9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": None, "min_x": {"$min": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "min_x": "2"}],
        msg="$min should use collation ordering (binary min would be '10')",
    ),
    CommandTestCase(
        "group_max_uses_collation",
        docs=[
            {"_id": 1, "x": "10"},
            {"_id": 2, "x": "2"},
            {"_id": 3, "x": "9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": None, "max_x": {"$max": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "max_x": "10"}],
        msg="$max should use collation ordering (binary max would be '9')",
    ),
    CommandTestCase(
        "group_min_case_insensitive",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "B"},
            {"_id": 3, "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": None, "min_x": {"$min": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "min_x": "a"}],
        msg="$min with strength 1 should use linguistic ordering (binary min would be 'B')",
    ),
    CommandTestCase(
        "group_max_case_insensitive",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "B"},
            {"_id": 3, "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": None, "max_x": {"$max": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "max_x": "c"}],
        msg="$max with strength 1 should use linguistic ordering"
        " (binary max would be 'c' but min would differ)",
    ),
    CommandTestCase(
        "group_first_unaffected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": None, "first_x": {"$first": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "first_x": "apple"}],
        msg="$first should return the first document value regardless of collation",
    ),
    CommandTestCase(
        "group_last_unaffected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": None, "last_x": {"$last": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "last_x": "APPLE"}],
        msg="$last should return the last document value regardless of collation",
    ),
    CommandTestCase(
        "group_push_unaffected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": None, "all_x": {"$push": "$x"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "all_x": ["apple", "Apple", "APPLE"]}],
        msg="$push should preserve all values regardless of collation",
    ),
]

# Property [Compound Group Key Deduplication]: collation affects all string
# fields in a compound $group _id, collapsing case/accent variants across
# every field in the compound key.
COLLATION_GROUP_COMPOUND_KEY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "group_compound_strength1_collapses_both_fields",
        docs=[
            {"_id": 1, "x": "apple", "y": "red"},
            {"_id": 2, "x": "Apple", "y": "Red"},
            {"_id": 3, "x": "apple", "y": "green"},
            {"_id": 4, "x": "banana", "y": "yellow"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": {"x": "$x", "y": "$y"}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": {"x": "apple", "y": "green"}, "count": 1},
            {"_id": {"x": "apple", "y": "red"}, "count": 2},
            {"_id": {"x": "banana", "y": "yellow"}, "count": 1},
        ],
        msg="$group with compound _id and strength 1 should collapse case variants in all fields",
    ),
    CommandTestCase(
        "group_compound_no_collation_all_distinct",
        docs=[
            {"_id": 1, "x": "apple", "y": "red"},
            {"_id": 2, "x": "Apple", "y": "Red"},
            {"_id": 3, "x": "apple", "y": "green"},
            {"_id": 4, "x": "banana", "y": "yellow"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": {"x": "$x", "y": "$y"}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[
            {"_id": {"x": "Apple", "y": "Red"}, "count": 1},
            {"_id": {"x": "apple", "y": "green"}, "count": 1},
            {"_id": {"x": "apple", "y": "red"}, "count": 1},
            {"_id": {"x": "banana", "y": "yellow"}, "count": 1},
        ],
        msg="$group with compound _id without collation should treat all case variants as distinct",
    ),
    CommandTestCase(
        "group_compound_second_field_distinguishes",
        docs=[
            {"_id": 1, "x": "apple", "y": "red"},
            {"_id": 2, "x": "Apple", "y": "blue"},
            {"_id": 3, "x": "apple", "y": "Red"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": {"x": "$x", "y": "$y"}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": {"x": "Apple", "y": "blue"}, "count": 1},
            {"_id": {"x": "apple", "y": "red"}, "count": 2},
        ],
        msg="$group with compound _id should use collation on second field to distinguish groups",
    ),
]

COLLATION_AGGREGATE_GROUP_TESTS: list[CommandTestCase] = (
    COLLATION_GROUP_KEY_TESTS
    + COLLATION_GROUP_ACCUMULATOR_TESTS
    + COLLATION_GROUP_COMPOUND_KEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_GROUP_TESTS))
def test_collation_aggregate_group(database_client, collection, test):
    """Test collation effects on $group key deduplication and accumulators."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
