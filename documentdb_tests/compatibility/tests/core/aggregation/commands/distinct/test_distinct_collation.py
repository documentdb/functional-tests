"""Tests for distinct command collation behavior."""

from __future__ import annotations

from typing import Any

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CustomCollection,
    ViewOnCustomCollection,
)

# Property [Collation Effects on Deduplication]: collation affects which values
# are considered duplicates during distinct.
DISTINCT_COLLATION_DEDUP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_basic_string_dedup",
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "APPLE"}, {"_id": 3, "x": "banana"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["apple", "banana"], "ok": 1.0},
        msg="distinct should collapse case-equivalent strings under case-insensitive collation",
    ),
    CommandTestCase(
        "collation_nested_array_dedup",
        docs=[{"_id": 1, "x": [["hello"]]}, {"_id": 2, "x": [["HELLO"]]}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": [["hello"]], "ok": 1.0},
        msg=(
            "distinct should collapse nested arrays containing"
            " case-equivalent strings under collation"
        ),
    ),
    CommandTestCase(
        "collation_nested_object_dedup",
        docs=[
            {"_id": 1, "x": {"name": "hello"}},
            {"_id": 2, "x": {"name": "HELLO"}},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": [{"name": "hello"}], "ok": 1.0},
        msg="distinct should collapse objects with case-equivalent string values under collation",
    ),
    CommandTestCase(
        "collation_after_array_unwinding",
        docs=[
            {"_id": 1, "x": ["hello", "world"]},
            {"_id": 2, "x": ["HELLO", "WORLD"]},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["hello", "world"], "ok": 1.0},
        msg="distinct should apply collation dedup to individual array elements after unwinding",
    ),
    CommandTestCase(
        "collation_non_string_unaffected",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": "a"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": None},
            {"_id": 5, "x": True},
            {"_id": 6, "x": False},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": [None, 1, "a", False, True], "ok": 1.0},
        msg=(
            "distinct should not collapse non-string elements"
            " (numbers, null, booleans) under collation"
        ),
    ),
    CommandTestCase(
        "collation_regex_unaffected",
        docs=[
            {"_id": 1, "x": Regex("hello", "")},
            {"_id": 2, "x": Regex("HELLO", "")},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={
            "values": [Regex("HELLO", ""), Regex("hello", "")],
            "ok": 1.0,
        },
        msg="distinct should not collapse regex values under collation",
    ),
    CommandTestCase(
        "collation_first_encountered_wins",
        docs=[
            {"_id": 1, "x": "Hello"},
            {"_id": 2, "x": "HELLO"},
            {"_id": 3, "x": "hello"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["Hello"], "ok": 1.0},
        msg=(
            "distinct should return the first-encountered value"
            " when collation collapses duplicates"
        ),
    ),
]

# Property [Collation Inheritance]: the collection's default collation is used
# when no explicit collation is specified.
DISTINCT_COLLATION_INHERITANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "inherit_collation_omitted",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "APPLE"}, {"_id": 3, "x": "banana"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": ["apple", "banana"], "ok": 1.0},
        msg="distinct should use collection's default collation when collation is omitted",
    ),
    CommandTestCase(
        "inherit_collation_null",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "APPLE"}, {"_id": 3, "x": "banana"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "collation": None},
        expected={"values": ["apple", "banana"], "ok": 1.0},
        msg="distinct should use collection's default collation when collation is null",
    ),
    CommandTestCase(
        "inherit_collation_empty_doc",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "APPLE"}, {"_id": 3, "x": "banana"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "collation": {}},
        expected={"values": ["apple", "banana"], "ok": 1.0},
        msg="distinct should use collection's default collation when collation is empty doc",
    ),
    CommandTestCase(
        "inherit_key_always_case_sensitive",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "Name": "alice"}, {"_id": 2, "name": "bob"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "Name"},
        expected={"values": ["alice"], "ok": 1.0},
        msg="distinct key field path matching should be case-sensitive regardless of collation",
    ),
    CommandTestCase(
        "inherit_explicit_overrides_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "APPLE"}, {"_id": 3, "x": "banana"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"values": ["apple", "APPLE", "banana"], "ok": 1.0},
        msg="distinct should use explicit collation over collection default when specified",
    ),
]

# Property [Collation Effects on Ordering]: collation changes the sort order of
# results from binary comparison to locale-aware ordering.
DISTINCT_COLLATION_ORDERING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_ordering_locale_aware",
        docs=[
            {"_id": 1, "x": "Banana"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "Cherry"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en"},
        },
        expected={"values": ["apple", "Banana", "Cherry"], "ok": 1.0},
        msg=(
            "distinct with collation should order results by locale-aware comparison"
            " instead of binary comparison"
        ),
    ),
    CommandTestCase(
        "collation_ordering_binary_default",
        docs=[
            {"_id": 1, "x": "Banana"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "Cherry"},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": ["Banana", "Cherry", "apple"], "ok": 1.0},
        msg="distinct without collation should order results by binary comparison",
    ),
]

# Property [Collation Affects Query Matching]: the collation parameter applies
# to the query filter, not just deduplication.
DISTINCT_COLLATION_QUERY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_query_case_insensitive_match",
        docs=[
            {"_id": 1, "x": "val1", "status": "Active"},
            {"_id": 2, "x": "val2", "status": "active"},
            {"_id": 3, "x": "val3", "status": "INACTIVE"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"status": "active"},
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["val1", "val2"], "ok": 1.0},
        msg=(
            "distinct should apply collation to query filter matching,"
            " allowing case-insensitive comparison"
        ),
    ),
    CommandTestCase(
        "collation_query_without_collation_exact_match",
        docs=[
            {"_id": 1, "x": "val1", "status": "Active"},
            {"_id": 2, "x": "val2", "status": "active"},
            {"_id": 3, "x": "val3", "status": "INACTIVE"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"status": "active"},
        },
        expected={"values": ["val2"], "ok": 1.0},
        msg="distinct without collation should match query filter exactly",
    ),
]

# Property [Collation Inheritance on Views]: views without an explicit collation
# use simple binary comparison, not the source collection's collation.
DISTINCT_COLLATION_INHERITANCE_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "inherit_view_no_inherit",
        target_collection=ViewOnCustomCollection(
            source_options={"collation": {"locale": "en", "strength": 1}}
        ),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "APPLE"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": sorted(["APPLE", "apple", "banana"]), "ok": 1},
        ignore_order_in=["values"],
        msg=(
            "distinct on a view should use binary comparison,"
            " not the source collection's collation"
        ),
    ),
]

DISTINCT_COLLATION_TESTS: list[CommandTestCase] = (
    DISTINCT_COLLATION_DEDUP_TESTS
    + DISTINCT_COLLATION_INHERITANCE_TESTS
    + DISTINCT_COLLATION_ORDERING_TESTS
    + DISTINCT_COLLATION_QUERY_TESTS
    + DISTINCT_COLLATION_INHERITANCE_VIEW_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_COLLATION_TESTS))
def test_distinct_collation(database_client: Any, collection: Any, test: CommandTestCase) -> None:
    """Test distinct collation cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
