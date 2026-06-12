"""Tests for collation semantics in the distinct command.

Tests collation-specific behaviors (strength levels, accent handling, numeric
ordering) that go beyond basic wiring validation covered in the distinct
command tests.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Distinct Strength Semantics]: different strength levels produce
# different deduplication behavior - strength 1 collapses accents and case,
# strength 3 preserves all variants.
COLLATION_DISTINCT_STRENGTH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "strength1_accent_insensitive",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "caf\u00e9"},
            {"_id": 3, "x": "other"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["cafe", "other"], "ok": 1.0},
        msg="distinct with strength 1 should deduplicate accent variants",
    ),
    CommandTestCase(
        "strength3_preserves_all",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"values": ["apple", "Apple", "APPLE"], "ok": 1.0},
        ignore_order_in=["values"],
        msg="distinct with strength 3 should preserve case-distinct values",
    ),
]

# Property [Distinct Query Filter with Non-String Predicate]: collation affects
# deduplication even when the query filter uses non-string comparisons.
COLLATION_DISTINCT_QUERY_SEMANTIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_non_string_filter_with_collation_dedup",
        docs=[
            {"_id": 1, "x": "apple", "n": 1},
            {"_id": 2, "x": "Apple", "n": 2},
            {"_id": 3, "x": "banana", "n": 3},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$gt": 1}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"values": ["Apple", "banana"], "ok": 1.0},
        msg="distinct should apply collation to deduplication even with non-string query",
    ),
]

# Property [Distinct Numeric Ordering]: numericOrdering affects the ordering
# of distinct results that contain embedded numeric substrings.
COLLATION_DISTINCT_NUMERIC_ORDERING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "numeric_ordering_dedup",
        docs=[
            {"_id": 1, "x": "file2"},
            {"_id": 2, "x": "file10"},
            {"_id": 3, "x": "file1"},
            {"_id": 4, "x": "file2"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected={"values": ["file1", "file2", "file10"], "ok": 1.0},
        msg="distinct with numericOrdering should order embedded numbers numerically",
    ),
]

# Property [Distinct Collection Default Collation]: when no explicit collation is
# specified, the distinct command uses the collection's default collation.
COLLATION_DISTINCT_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_default_deduplicates",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
        },
        expected={"values": ["apple", "banana"], "ok": 1.0},
        msg="distinct should use collection default collation for deduplication",
    ),
    CommandTestCase(
        "explicit_overrides_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"values": ["apple", "Apple", "banana"], "ok": 1.0},
        ignore_order_in=["values"],
        msg="distinct with explicit collation should override collection default",
    ),
]

COLLATION_DISTINCT_TESTS = (
    COLLATION_DISTINCT_STRENGTH_TESTS
    + COLLATION_DISTINCT_QUERY_SEMANTIC_TESTS
    + COLLATION_DISTINCT_NUMERIC_ORDERING_TESTS
    + COLLATION_DISTINCT_DEFAULT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_DISTINCT_TESTS))
def test_collation_distinct(database_client, collection, test):
    """Test collation strength and ordering semantics in the distinct command."""
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
