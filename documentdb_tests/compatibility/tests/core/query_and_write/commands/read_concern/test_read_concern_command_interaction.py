"""
readConcern command interaction tests.

Verifies that readConcern works correctly with other command options
(sort, projection, limit, skip, query filters) and on empty/non-existent collections.
"""

import pytest

from documentdb_tests.compatibility.tests.core.query_and_write.commands.read_concern.utils import (
    is_cursor_command,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Command Option Interaction]: readConcern does not interfere with other command options.
INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_with_sort",
        docs=[{"_id": 1, "x": 3}, {"_id": 2, "x": 1}, {"_id": 3, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 2, "x": 1}, {"_id": 3, "x": 2}, {"_id": 1, "x": 3}],
        msg="find with readConcern should respect sort order.",
    ),
    CommandTestCase(
        "find_with_projection",
        docs=[{"_id": 1, "x": 1, "y": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "projection": {"x": 1, "_id": 0},
            "readConcern": {"level": "local"},
        },
        expected=[{"x": 1}],
        msg="find with readConcern should respect projection.",
    ),
    CommandTestCase(
        "find_with_limit",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "limit": 2,
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1}, {"_id": 2}],
        msg="find with readConcern should respect limit.",
    ),
    CommandTestCase(
        "find_with_skip",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "skip": 1,
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 2}, {"_id": 3}],
        msg="find with readConcern should respect skip.",
    ),
    CommandTestCase(
        "find_with_expr_filter",
        docs=[{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 2, "b": 4}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$gt": ["$a", "$b"]}},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "a": 5, "b": 3}],
        msg="find with readConcern should support $expr filter.",
    ),
    CommandTestCase(
        "aggregate_with_multiple_stages",
        docs=[
            {"_id": 1, "x": 1, "g": "a"},
            {"_id": 2, "x": 2, "g": "a"},
            {"_id": 3, "x": 3, "g": "b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"g": "a"}}, {"$sort": {"x": -1}}, {"$limit": 1}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected=[{"_id": 2, "x": 2, "g": "a"}],
        msg="aggregate with readConcern should work with multiple stages.",
    ),
    CommandTestCase(
        "distinct_with_query",
        docs=[
            {"_id": 1, "x": 1, "active": True},
            {"_id": 2, "x": 2, "active": False},
            {"_id": 3, "x": 1, "active": True},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"active": True},
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0, "values": [1]},
        msg="distinct with readConcern should respect query filter.",
    ),
    CommandTestCase(
        "count_with_query",
        docs=[{"_id": 1, "s": "a"}, {"_id": 2, "s": "b"}, {"_id": 3, "s": "a"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"s": "a"},
            "readConcern": {"level": "available"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with readConcern should respect query filter.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INTERACTION_TESTS))
def test_read_concern_command_interaction(collection, test: CommandTestCase):
    """Test readConcern works correctly with other command options."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# Property [Empty Collection]: readConcern on an empty collection returns empty results.
EMPTY_COLLECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_on_empty_collection",
        docs=[],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "readConcern": {"level": "local"},
        },
        expected=[],
        msg="find with readConcern on empty collection should return empty.",
    ),
    CommandTestCase(
        "aggregate_on_empty_collection",
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected=[],
        msg="aggregate with readConcern on empty collection should return empty.",
    ),
    CommandTestCase(
        "count_on_empty_collection",
        docs=[],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
            "readConcern": {"level": "local"},
        },
        expected={"n": 0, "ok": 1.0},
        msg="count with readConcern on empty collection should return zero.",
    ),
    CommandTestCase(
        "distinct_on_empty_collection",
        docs=[],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0, "values": []},
        msg="distinct with readConcern on empty collection should return empty values.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMPTY_COLLECTION_TESTS))
def test_read_concern_on_empty_collection(collection, test: CommandTestCase):
    """Test readConcern on an empty collection returns empty results."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# Property [Non-Existent Collection]: non-existent collections return empty results.
def test_find_read_concern_on_nonexistent_collection(database_client):
    """Test find with readConcern on non-existent collection returns empty."""
    coll = database_client["nonexistent_rc_test_coll"]
    result = execute_command(
        coll,
        {"find": coll.name, "filter": {}, "readConcern": {"level": "local"}},
    )
    assertSuccess(
        result, [], msg="find with readConcern on non-existent collection should return empty."
    )


def test_count_read_concern_on_nonexistent_collection(database_client):
    """Test count with readConcern on non-existent collection returns zero."""
    coll = database_client["nonexistent_rc_test_coll"]
    result = execute_command(
        coll,
        {"count": coll.name, "query": {}, "readConcern": {"level": "local"}},
    )
    assertResult(
        result,
        expected={"n": 0, "ok": 1.0},
        msg="count with readConcern on non-existent collection should return zero.",
        raw_res=True,
    )


def test_aggregate_read_concern_on_nonexistent_collection(database_client):
    """Test aggregate with readConcern on non-existent collection returns empty."""
    coll = database_client["nonexistent_rc_test_coll"]
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
    )
    assertSuccess(
        result, [], msg="aggregate with readConcern on non-existent collection should return empty."
    )


def test_distinct_read_concern_on_nonexistent_collection(database_client):
    """Test distinct with readConcern on non-existent collection returns empty values."""
    coll = database_client["nonexistent_rc_test_coll"]
    result = execute_command(
        coll,
        {"distinct": coll.name, "key": "x", "readConcern": {"level": "local"}},
    )
    assertResult(
        result,
        expected={"ok": 1.0, "values": []},
        msg="distinct with readConcern on non-existent collection should return empty values.",
        raw_res=True,
    )
