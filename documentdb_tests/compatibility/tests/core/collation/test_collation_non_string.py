"""Tests for non-string values being unaffected by collation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-String Values Unaffected]: non-string types use BSON type
# ordering regardless of collation settings, and collation only affects
# string-to-string comparisons.
COLLATION_NON_STRING_UNAFFECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "nonstring_sort_bson_type_order",
        docs=[
            {"_id": 1, "x": 42},
            {"_id": 2, "x": True},
            {"_id": 3, "x": None},
            {"_id": 4, "x": "hello"},
            {"_id": 5, "x": ObjectId("000000000000000000000001")},
            {"_id": 6, "x": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 3, "x": None},
            {"_id": 1, "x": 42},
            {"_id": 4, "x": "hello"},
            {"_id": 5, "x": ObjectId("000000000000000000000001")},
            {"_id": 2, "x": True},
            {"_id": 6, "x": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        ],
        msg="non-string types should sort in BSON type order regardless of collation",
    ),
    CommandTestCase(
        "nonstring_sort_numeric_values",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2, "x": 2},
            {"_id": 3, "x": Int64(100)},
            {"_id": 4, "x": 1.5},
            {"_id": 5, "x": Decimal128("3")},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 4, "x": 1.5},
            {"_id": 2, "x": 2},
            {"_id": 5, "x": Decimal128("3")},
            {"_id": 1, "x": 10},
            {"_id": 3, "x": Int64(100)},
        ],
        msg="numeric values should sort by value regardless of collation",
    ),
    CommandTestCase(
        "nonstring_null_missing_before_empty_string",
        docs=[
            {"_id": 1, "x": ""},
            {"_id": 2, "x": None},
            {"_id": 3},
            {"_id": 4, "x": "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 2, "x": None},
            {"_id": 3},
            {"_id": 1, "x": ""},
            {"_id": 4, "x": "a"},
        ],
        msg="null and missing should sort before empty string in collation-aware sort",
    ),
    CommandTestCase(
        "nonstring_match_null_matches_null_and_missing",
        docs=[
            {"_id": 1, "x": "hello"},
            {"_id": 2, "x": None},
            {"_id": 3},
            {"_id": 4, "x": 42},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": None}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 2, "x": None},
            {"_id": 3},
        ],
        msg="$match with null should match both null and missing regardless of collation",
    ),
    CommandTestCase(
        "nonstring_group_null_and_missing_together",
        docs=[
            {"_id": 1, "x": None, "v": 10},
            {"_id": 2, "v": 20},
            {"_id": 3, "x": "a", "v": 30},
            {"_id": 4, "x": "A", "v": 40},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": "$x", "total": {"$sum": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": None, "total": 30},
            {"_id": "a", "total": 70},
        ],
        msg="$group should group null and missing values together regardless of collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_NON_STRING_UNAFFECTED_TESTS))
def test_collation_non_string(database_client, collection, test):
    """Test that non-string values are unaffected by collation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
