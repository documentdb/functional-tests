"""Tests for collation effects on dotted (nested) field paths."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Dotted Path Filter Matching]: collation affects equality and
# comparison operators on dotted field paths in find and aggregate $match,
# enabling case-insensitive matching on nested document fields.
COLLATION_DOTTED_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_dotted_eq_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 3, "a": {"b": "banana"}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a.b": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
        ],
        msg="find on dotted path with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "find_dotted_gt_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Banana"}},
            {"_id": 3, "a": {"b": "cherry"}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a.b": {"$gt": "apple"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "a": {"b": "Banana"}},
            {"_id": 3, "a": {"b": "cherry"}},
        ],
        msg="find $gt on dotted path should use collation",
    ),
    CommandTestCase(
        "find_dotted_in_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 3, "a": {"b": "banana"}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a.b": {"$in": ["APPLE"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
        ],
        msg="find $in on dotted path should use collation",
    ),
    CommandTestCase(
        "find_deeply_nested_eq",
        docs=[
            {"_id": 1, "a": {"b": {"c": "apple"}}},
            {"_id": 2, "a": {"b": {"c": "Apple"}}},
            {"_id": 3, "a": {"b": {"c": "banana"}}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a.b.c": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "a": {"b": {"c": "apple"}}},
            {"_id": 2, "a": {"b": {"c": "Apple"}}},
        ],
        msg="find on deeply nested dotted path should use collation",
    ),
    CommandTestCase(
        "match_dotted_eq_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 3, "a": {"b": "banana"}},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"a.b": "apple"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
        ],
        msg="$match on dotted path should use collation",
    ),
    CommandTestCase(
        "find_dotted_no_collation_binary",
        docs=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a.b": "apple"},
        },
        expected=[{"_id": 1, "a": {"b": "apple"}}],
        msg="find on dotted path without collation should use binary comparison",
    ),
]

# Property [Dotted Path Sort Ordering]: collation affects sort ordering when
# sorting on dotted field paths.
COLLATION_DOTTED_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_dotted_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "banana"}},
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 3, "a": {"b": "cherry"}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"a.b": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 1, "a": {"b": "banana"}},
            {"_id": 3, "a": {"b": "cherry"}},
        ],
        msg="find sort on dotted path should use collation for case-insensitive ordering",
    ),
    CommandTestCase(
        "sort_dotted_numeric_ordering",
        docs=[
            {"_id": 1, "a": {"b": "file10"}},
            {"_id": 2, "a": {"b": "file2"}},
            {"_id": 3, "a": {"b": "file1"}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"a.b": 1},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 3, "a": {"b": "file1"}},
            {"_id": 2, "a": {"b": "file2"}},
            {"_id": 1, "a": {"b": "file10"}},
        ],
        msg="find sort on dotted path should use collation numericOrdering",
    ),
    CommandTestCase(
        "sort_deeply_nested",
        docs=[
            {"_id": 1, "a": {"b": {"c": "banana"}}},
            {"_id": 2, "a": {"b": {"c": "Apple"}}},
            {"_id": 3, "a": {"b": {"c": "cherry"}}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"a.b.c": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "a": {"b": {"c": "Apple"}}},
            {"_id": 1, "a": {"b": {"c": "banana"}}},
            {"_id": 3, "a": {"b": {"c": "cherry"}}},
        ],
        msg="find sort on deeply nested dotted path should use collation",
    ),
    CommandTestCase(
        "aggregate_sort_dotted",
        docs=[
            {"_id": 1, "a": {"b": "banana"}},
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 3, "a": {"b": "cherry"}},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"a.b": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 1, "a": {"b": "banana"}},
            {"_id": 3, "a": {"b": "cherry"}},
        ],
        msg="aggregate $sort on dotted path should use collation",
    ),
]

# Property [Dotted Path in Update Filter]: collation affects the filter on
# dotted paths in update commands.
COLLATION_DOTTED_UPDATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_dotted_filter_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "apple"}, "v": 1},
            {"_id": 2, "a": {"b": "Apple"}, "v": 1},
            {"_id": 3, "a": {"b": "banana"}, "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"a.b": "apple"},
                    "u": {"$set": {"v": 2}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="update on dotted path filter should use collation",
    ),
]

# Property [Dotted Path in Distinct]: collation affects deduplication on dotted
# field paths.
COLLATION_DOTTED_DISTINCT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "distinct_dotted_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 3, "a": {"b": "banana"}},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "a.b",
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"values": ["apple", "banana"], "ok": 1.0},
        msg="distinct on dotted path should use collation for deduplication",
    ),
]

COLLATION_DOTTED_PATH_TESTS: list[CommandTestCase] = (
    COLLATION_DOTTED_FILTER_TESTS
    + COLLATION_DOTTED_SORT_TESTS
    + COLLATION_DOTTED_UPDATE_TESTS
    + COLLATION_DOTTED_DISTINCT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_DOTTED_PATH_TESTS))
def test_collation_dotted_paths(database_client, collection, test):
    """Test collation effects on dotted field paths."""
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
