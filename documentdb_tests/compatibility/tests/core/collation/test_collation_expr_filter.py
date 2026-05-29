"""Tests for collation with $expr in find, update, and delete command filters."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Find $expr with Collation]: $expr in the find command filter uses
# command-level collation for expression operators like $eq, $cmp, $gt.
COLLATION_FIND_EXPR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_expr_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$x", "apple"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="find $expr $eq with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "find_expr_gt_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$gt": ["$x", "apple"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="find $expr $gt with strength 2 should compare case-insensitively",
    ),
    CommandTestCase(
        "find_expr_cmp_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": [{"$cmp": ["$x", "apple"]}, 0]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="find $expr $cmp with strength 2 should compare case-insensitively",
    ),
    CommandTestCase(
        "find_expr_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$x", "apple"]}},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find $expr without collation should use binary comparison",
    ),
    CommandTestCase(
        "find_expr_in_field_ref_no_collation",
        docs=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$in": ["$x", ["Apple", "Banana"]]}},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="find $expr $in with field ref first arg should not use collation",
    ),
    CommandTestCase(
        "find_expr_in_literal_uses_collation",
        docs=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$in": ["apple", "$arr"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        msg="find $expr $in with literal first arg should use collation",
    ),
]

# Property [Update and Delete $expr Filter with Collation]: $expr in update and
# delete filters uses per-statement collation for expression evaluation.
COLLATION_WRITE_EXPR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_expr_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"$expr": {"$eq": ["$x", "apple"]}},
                    "u": {"$set": {"v": 2}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="update $expr filter with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "update_expr_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"$expr": {"$eq": ["$x", "apple"]}},
                    "u": {"$set": {"v": 2}},
                    "multi": True,
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="update $expr filter without collation should use binary comparison",
    ),
    CommandTestCase(
        "delete_expr_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"$expr": {"$eq": ["$x", "apple"]}},
                    "limit": 0,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete $expr filter with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "delete_expr_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"$expr": {"$eq": ["$x", "apple"]}},
                    "limit": 0,
                }
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete $expr filter without collation should use binary comparison",
    ),
]

COLLATION_EXPR_FILTER_TESTS: list[CommandTestCase] = (
    COLLATION_FIND_EXPR_TESTS + COLLATION_WRITE_EXPR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_EXPR_FILTER_TESTS))
def test_collation_expr_filter(database_client, collection, test):
    """Test collation behavior with $expr in find, update, and delete filters."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = test.build_expected(ctx)
    assertResult(
        result,
        expected=expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(expected, list),
    )
