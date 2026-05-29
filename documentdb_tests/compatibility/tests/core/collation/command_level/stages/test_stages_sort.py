"""Tests for collation effects on sort, sortArray, and sortByCount stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sort Stage Multiple Sorts]: multiple $sort stages in one pipeline
# all use the command-level collation.
COLLATION_SORT_STAGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_stage_multiple_sorts_use_collation",
        docs=[
            {"_id": 1, "x": "B", "y": "cherry"},
            {"_id": 2, "x": "a", "y": "Banana"},
            {"_id": 3, "x": "A", "y": "apple"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"x": 1}},
                {"$limit": 2},
                {"$sort": {"y": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        # Binary sort would give Banana < apple (B=66 < a=97), but
        # strength 2 gives apple < Banana (case-insensitive alphabetical).
        expected=[
            {"_id": 3, "x": "A", "y": "apple"},
            {"_id": 2, "x": "a", "y": "Banana"},
        ],
        msg="multiple $sort stages in one pipeline should all use command-level collation",
    ),
]

# Property [$sortArray Collation]: $sortArray respects command-level collation
# for ordering elements within the array.
COLLATION_SORTARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sortarray_strength1_case_insensitive",
        docs=[{"_id": 1, "items": ["banana", "Apple", "cherry", "apple", "BANANA"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"sorted": {"$sortArray": {"input": "$items", "sortBy": 1}}}}
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Strength 1 treats case variants as equivalent; stable sort preserves
        # insertion order for ties.
        expected=[{"_id": 1, "sorted": ["Apple", "apple", "banana", "BANANA", "cherry"]}],
        msg="$sortArray should use collation strength 1 for case-insensitive ordering",
    ),
    CommandTestCase(
        "sortarray_strength3_case_sensitive",
        docs=[{"_id": 1, "items": ["banana", "Apple", "cherry", "apple", "BANANA"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"sorted": {"$sortArray": {"input": "$items", "sortBy": 1}}}}
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "sorted": ["apple", "Apple", "banana", "BANANA", "cherry"]}],
        msg="$sortArray should use collation strength 3 for case-sensitive ordering",
    ),
    CommandTestCase(
        "sortarray_no_collation_binary",
        docs=[{"_id": 1, "items": ["banana", "Apple", "cherry", "apple", "BANANA"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"sorted": {"$sortArray": {"input": "$items", "sortBy": 1}}}}
            ],
            "cursor": {},
        },
        # Binary comparison: uppercase letters (A=65, B=66) sort before
        # lowercase (a=97, b=98).
        expected=[{"_id": 1, "sorted": ["Apple", "BANANA", "apple", "banana", "cherry"]}],
        msg="$sortArray without collation should use binary sort order",
    ),
    CommandTestCase(
        "sortarray_numeric_ordering",
        docs=[{"_id": 1, "items": ["item2", "item10", "item1"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"sorted": {"$sortArray": {"input": "$items", "sortBy": 1}}}}
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": 1, "sorted": ["item1", "item2", "item10"]}],
        msg="$sortArray should respect numericOrdering collation option",
    ),
    CommandTestCase(
        "sortarray_objects_case_insensitive",
        docs=[
            {
                "_id": 1,
                "items": [
                    {"name": "a", "v": 1},
                    {"name": "B", "v": 2},
                    {"name": "c", "v": 3},
                ],
            }
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"sorted": {"$sortArray": {"input": "$items", "sortBy": {"name": 1}}}}}
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {
                "_id": 1,
                "sorted": [
                    {"name": "a", "v": 1},
                    {"name": "B", "v": 2},
                    {"name": "c", "v": 3},
                ],
            }
        ],
        msg="$sortArray on objects should use collation for field-based sort",
    ),
    CommandTestCase(
        "sortarray_objects_no_collation_binary",
        docs=[
            {
                "_id": 1,
                "items": [
                    {"name": "a", "v": 1},
                    {"name": "B", "v": 2},
                    {"name": "c", "v": 3},
                ],
            }
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"sorted": {"$sortArray": {"input": "$items", "sortBy": {"name": 1}}}}}
            ],
            "cursor": {},
        },
        expected=[
            {
                "_id": 1,
                "sorted": [
                    {"name": "B", "v": 2},
                    {"name": "a", "v": 1},
                    {"name": "c", "v": 3},
                ],
            }
        ],
        msg="$sortArray on objects without collation should use binary field sort",
    ),
]

# Property [sortByCount Grouping]: collation affects grouping in $sortByCount
# so that collation-equal strings collapse into one group with the
# first-encountered value as the key.
COLLATION_SORT_BY_COUNT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_by_count_strength1_collapse",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$sortByCount": "$x"},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": "cafe", "count": 3},
            {"_id": "banana", "count": 1},
        ],
        msg="$sortByCount with strength 1 should collapse all case and accent variants",
    ),
    CommandTestCase(
        "sort_by_count_strength2_accent_distinct",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
            {"_id": 4, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$sortByCount": "$x"},
                {"$sort": {"count": -1, "_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": "cafe", "count": 2},
            {"_id": "banana", "count": 1},
            {"_id": "caf\u00e9", "count": 1},
        ],
        msg="$sortByCount with strength 2 should collapse case but keep accents distinct",
    ),
    CommandTestCase(
        "sort_by_count_strength3_all_distinct",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "cafe"},
            {"_id": 3, "x": "cafe"},
            {"_id": 4, "x": "Cafe"},
            {"_id": 5, "x": "Cafe"},
            {"_id": 6, "x": "caf\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$sortByCount": "$x"},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": "cafe", "count": 3},
            {"_id": "Cafe", "count": 2},
            {"_id": "caf\u00e9", "count": 1},
        ],
        msg="$sortByCount with strength 3 should treat all variants as distinct groups",
    ),
]

# Property [Multi-Field Sort with Collation]: collation applies to all string
# fields in a compound sort key, not just the primary sort field.
COLLATION_MULTI_FIELD_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_multi_field_collation_both_keys",
        docs=[
            {"_id": 1, "x": "a", "y": "B"},
            {"_id": 2, "x": "A", "y": "b"},
            {"_id": 3, "x": "a", "y": "a"},
            {"_id": 4, "x": "A", "y": "A"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1, "y": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        # Strength 2: x values all equal (case-insensitive), so sort falls
        # through to y. y: a/A (equal) < b/B (equal). Stable sort preserves
        # insertion order within ties.
        expected=[
            {"_id": 3, "x": "a", "y": "a"},
            {"_id": 4, "x": "A", "y": "A"},
            {"_id": 1, "x": "a", "y": "B"},
            {"_id": 2, "x": "A", "y": "b"},
        ],
        msg="multi-field sort with collation should apply collation to both sort keys",
    ),
    CommandTestCase(
        "sort_multi_field_no_collation_binary",
        docs=[
            {"_id": 1, "x": "a", "y": "B"},
            {"_id": 2, "x": "A", "y": "b"},
            {"_id": 3, "x": "a", "y": "a"},
            {"_id": 4, "x": "A", "y": "A"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1, "y": 1}}],
            "cursor": {},
        },
        # Binary: 'A'(65) < 'a'(97). Within x='A': 'A'(65) < 'b'(98).
        # Within x='a': 'B'(66) < 'a'(97).
        expected=[
            {"_id": 4, "x": "A", "y": "A"},
            {"_id": 2, "x": "A", "y": "b"},
            {"_id": 1, "x": "a", "y": "B"},
            {"_id": 3, "x": "a", "y": "a"},
        ],
        msg="multi-field sort without collation should use binary comparison on both keys",
    ),
    CommandTestCase(
        "sort_multi_field_strength3_distinguishes",
        docs=[
            {"_id": 1, "x": "a", "y": "B"},
            {"_id": 2, "x": "A", "y": "b"},
            {"_id": 3, "x": "a", "y": "a"},
            {"_id": 4, "x": "A", "y": "A"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1, "y": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        # Strength 3: x: 'a' < 'A'. Within x='a': y: 'a' < 'B'.
        # Within x='A': y: 'A' < 'b'.
        expected=[
            {"_id": 3, "x": "a", "y": "a"},
            {"_id": 1, "x": "a", "y": "B"},
            {"_id": 4, "x": "A", "y": "A"},
            {"_id": 2, "x": "A", "y": "b"},
        ],
        msg="multi-field sort with strength 3 should distinguish case in both keys",
    ),
]

COLLATION_AGGREGATE_SORT_STAGES_TESTS: list[CommandTestCase] = (
    COLLATION_SORT_STAGE_TESTS
    + COLLATION_SORTARRAY_TESTS
    + COLLATION_SORT_BY_COUNT_TESTS
    + COLLATION_MULTI_FIELD_SORT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_SORT_STAGES_TESTS))
def test_collation_aggregate_sort_stages(database_client, collection, test):
    """Test collation effects on $sort, $sortArray, and $sortByCount stages."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
