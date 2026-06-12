"""Tests for collation effects on expressions within $replaceRoot and $replaceWith."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [ReplaceRoot Expression Collation]: expressions within $replaceRoot
# and $replaceWith that perform string comparisons use command-level collation.
COLLATION_REPLACEROOT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "replaceroot_cond_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "Apple", "a": {"v": 1}, "b": {"v": 2}},
            {"_id": 2, "x": "banana", "a": {"v": 3}, "b": {"v": 4}},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$replaceRoot": {"newRoot": {"$cond": [{"$eq": ["$x", "apple"]}, "$a", "$b"]}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"v": 1}, {"v": 4}],
        msg="$replaceRoot $cond $eq should use collation",
    ),
    CommandTestCase(
        "replaceroot_no_collation_binary",
        docs=[
            {"_id": 1, "x": "Apple", "a": {"v": 1}, "b": {"v": 2}},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$replaceRoot": {"newRoot": {"$cond": [{"$eq": ["$x", "apple"]}, "$a", "$b"]}}},
            ],
            "cursor": {},
        },
        expected=[{"v": 2}],
        msg="$replaceRoot without collation should use binary comparison",
    ),
    CommandTestCase(
        "replacewith_cond_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "Apple", "a": {"v": 1}, "b": {"v": 2}},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$replaceWith": {"$cond": [{"$eq": ["$x", "apple"]}, "$a", "$b"]}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"v": 1}],
        msg="$replaceWith $cond $eq should use collation",
    ),
    CommandTestCase(
        "replaceroot_filter_expr_case_insensitive",
        docs=[
            {"_id": 1, "items": ["Apple", "banana", "Cherry"], "target": "apple"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "matched": {
                                "$filter": {
                                    "input": "$items",
                                    "as": "item",
                                    "cond": {"$eq": ["$$item", "$target"]},
                                }
                            }
                        }
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"matched": ["Apple"]}],
        msg="$replaceRoot with $filter expression should use collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_REPLACEROOT_TESTS))
def test_collation_aggregate_replaceroot(database_client, collection, test):
    """Test collation affects expressions within $replaceRoot/$replaceWith."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
