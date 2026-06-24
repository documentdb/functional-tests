"""
readConcern level 'local' availability and behavior tests.

Per the MongoDB spec, readConcern level 'local':
  - Is the default for reads against primary and secondaries.
  - Is available with or without causally consistent sessions and transactions.
  - Returns data from the local instance with no majority-write guarantee.

Tests in this file validate those availability and behavioral properties.
"""

import pytest

from documentdb_tests.compatibility.tests.core.query_and_write.commands.read_concern.utils import (
    is_cursor_command,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property [Local Is Default]: omitting readConcern is equivalent to level 'local'.
# Both sides (explicit 'local' and no readConcern) are each verified separately
# with one assertion per test, sharing the same expected value.
# ---------------------------------------------------------------------------

LOCAL_AS_EXPLICIT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_explicit_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="find with explicit readConcern 'local' should return all documents.",
    ),
    CommandTestCase(
        "aggregate_explicit_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"_id": 1}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="aggregate with explicit readConcern 'local' should return all documents.",
    ),
    CommandTestCase(
        "count_explicit_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
            "readConcern": {"level": "local"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with explicit readConcern 'local' should return total count.",
    ),
    CommandTestCase(
        "distinct_explicit_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0, "values": [1, 2]},
        msg="distinct with explicit readConcern 'local' should return distinct values.",
    ),
]

LOCAL_AS_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_omitted_read_concern",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"_id": 1},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="find without readConcern should return the same data as explicit 'local'.",
    ),
    CommandTestCase(
        "aggregate_omitted_read_concern",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"_id": 1}}],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="aggregate without readConcern should return the same data as explicit 'local'.",
    ),
    CommandTestCase(
        "count_omitted_read_concern",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count without readConcern should return the same result as explicit 'local'.",
    ),
    CommandTestCase(
        "distinct_omitted_read_concern",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
        },
        expected={"ok": 1.0, "values": [1, 2]},
        msg="distinct without readConcern should return the same result as explicit 'local'.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOCAL_AS_EXPLICIT_TESTS))
def test_read_concern_local_explicit(collection, test: CommandTestCase):
    """Test that explicit readConcern 'local' returns the expected results."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


@pytest.mark.parametrize("test", pytest_params(LOCAL_AS_DEFAULT_TESTS))
def test_read_concern_local_is_default(collection, test: CommandTestCase):
    """Test that omitting readConcern produces the same result as explicit 'local'."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# ---------------------------------------------------------------------------
# Property [Local Available Without Session]: level 'local' is available in
# a plain context — no session, no transaction, no replica set required.
# This validates the spec claim that 'local' is available unconditionally.
# ---------------------------------------------------------------------------

LOCAL_AVAILABILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_local_available_no_session",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}],
        msg="find with readConcern 'local' must be available without a session or transaction.",
    ),
    CommandTestCase(
        "aggregate_local_available_no_session",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"_id": 1}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}],
        msg="aggregate with readConcern 'local' must be available without a session or transaction.",  # noqa: E501
    ),
    CommandTestCase(
        "count_local_available_no_session",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
            "readConcern": {"level": "local"},
        },
        expected={"n": 3, "ok": 1.0},
        msg="count with readConcern 'local' must be available without a session or transaction.",
    ),
    CommandTestCase(
        "distinct_local_available_no_session",
        docs=[{"_id": 1, "cat": "x"}, {"_id": 2, "cat": "y"}, {"_id": 3, "cat": "x"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "cat",
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0, "values": ["x", "y"]},
        msg="distinct with readConcern 'local' must be available without a session or transaction.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOCAL_AVAILABILITY_TESTS))
def test_read_concern_local_available_without_session(collection, test: CommandTestCase):
    """Test readConcern 'local' is available without a session or transaction."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# ---------------------------------------------------------------------------
# Property [Local Reads Local State]: level 'local' returns the current state
# of the local instance immediately after a write, with no propagation delay.
# This confirms that freshly-inserted data is visible under 'local'.
# ---------------------------------------------------------------------------

LOCAL_READS_FRESH_DATA_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_local_sees_fresh_insert",
        docs=[{"_id": 1, "score": 100}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"score": 100},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "score": 100}],
        msg="find with readConcern 'local' must see data immediately after insert.",
    ),
    CommandTestCase(
        "aggregate_local_sees_fresh_insert",
        docs=[{"_id": 1, "score": 100}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"score": 100}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "score": 100}],
        msg="aggregate with readConcern 'local' must see data immediately after insert.",
    ),
    CommandTestCase(
        "count_local_sees_fresh_insert",
        docs=[{"_id": 1, "score": 100}, {"_id": 2, "score": 200}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"score": {"$gte": 100}},
            "readConcern": {"level": "local"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with readConcern 'local' must count freshly inserted documents.",
    ),
    CommandTestCase(
        "distinct_local_sees_fresh_insert",
        docs=[{"_id": 1, "tag": "new"}, {"_id": 2, "tag": "new"}, {"_id": 3, "tag": "old"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "tag",
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0, "values": ["new", "old"]},
        msg="distinct with readConcern 'local' must reflect freshly inserted values.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOCAL_READS_FRESH_DATA_TESTS))
def test_read_concern_local_reads_fresh_data(collection, test: CommandTestCase):
    """Test readConcern 'local' returns data immediately after a local write."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# ---------------------------------------------------------------------------
# Property [Local Reads Updated State]: level 'local' reflects updates to
# existing documents without any additional propagation requirement.
# ---------------------------------------------------------------------------


def test_find_local_sees_updated_document(collection):
    """Test find with readConcern 'local' reflects an in-place update immediately."""
    collection.insert_many([{"_id": 1, "status": "pending"}])

    # Update the document using a write command.
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"status": "done"}}}],
        },
    )

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"_id": 1},
            "readConcern": {"level": "local"},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1, "status": "done"}],
        msg="find with readConcern 'local' must reflect an update applied to the local instance.",
    )


def test_count_local_reflects_delete(collection):
    """Test count with readConcern 'local' reflects a deletion immediately."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])

    execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
        },
    )

    result = execute_command(
        collection,
        {
            "count": collection.name,
            "query": {},
            "readConcern": {"level": "local"},
        },
    )
    assertResult(
        result,
        expected={"n": 2, "ok": 1.0},
        msg="count with readConcern 'local' must reflect a deletion applied to the local instance.",
        raw_res=True,
    )
