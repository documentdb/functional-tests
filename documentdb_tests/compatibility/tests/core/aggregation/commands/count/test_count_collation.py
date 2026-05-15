"""Tests for count command collation behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Collation Behavior]: the collation option controls string comparison
# rules used during query evaluation.
COUNT_COLLATION_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_explicit_equality",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with case-insensitive collation should match both cases in equality",
    ),
    CommandTestCase(
        "collation_explicit_ne",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$ne": "abc"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count collation should affect $ne operator",
    ),
    CommandTestCase(
        "collation_explicit_in",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$in": ["abc"]}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count collation should affect $in operator",
    ),
    CommandTestCase(
        "collation_explicit_nin",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$nin": ["abc"]}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count collation should affect $nin operator",
    ),
    CommandTestCase(
        "collation_explicit_gt",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gt": "ABC"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count collation should affect $gt operator",
    ),
    CommandTestCase(
        "collation_explicit_gte",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$gte": "abc"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 3, "ok": 1.0},
        msg="count collation should affect $gte operator",
    ),
    CommandTestCase(
        "collation_explicit_lt",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$lt": "abc"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 0, "ok": 1.0},
        msg="count collation should affect $lt operator",
    ),
    CommandTestCase(
        "collation_explicit_lte",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$lte": "ABC"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count collation should affect $lte operator",
    ),
    CommandTestCase(
        "collation_explicit_expr",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$expr": {"$eq": ["$s", "abc"]}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count collation should affect $expr in query",
    ),
    CommandTestCase(
        "collation_regex_unaffected",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": {"$regex": "^abc$"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count collation should NOT affect $regex matching",
    ),
    CommandTestCase(
        "collation_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should use collection default collation when collation is omitted",
    ),
    CommandTestCase(
        "collation_null_uses_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": None,
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with collation=null should use collection default collation",
    ),
    CommandTestCase(
        "collation_empty_uses_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": {},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with collation={} should use collection default collation",
    ),
    CommandTestCase(
        "collation_simple_overrides_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "ABC"}, {"_id": 3, "s": "def"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "abc"},
            "collation": {"locale": "simple"},
        },
        expected={"n": 1, "ok": 1.0},
        msg='count with collation locale "simple" should override collection default',
    ),
]


@pytest.mark.parametrize("test", pytest_params(COUNT_COLLATION_BEHAVIOR_TESTS))
def test_count_collation(database_client, collection, test):
    """Test count command collation behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
