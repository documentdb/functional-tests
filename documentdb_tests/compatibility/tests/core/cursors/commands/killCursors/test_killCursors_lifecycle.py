"""Tests for killCursors cursor lifecycle and behavior."""

from __future__ import annotations

import datetime

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import CURSOR_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Behavior - Kill Active Cursors]: active cursors from
# find and aggregate are killed and reported in cursorsKilled.
KILLCURSORS_CORE_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        "kill_single_find_cursor",
        docs=[{"_id": i} for i in range(10)],
        cursor_count=1,
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [ctx.cursors[0]],
        },
        expected=lambda ctx: {
            "cursorsKilled": [ctx.cursors[0]],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill a single find cursor",
    ),
    CursorCommandTestCase(
        "batch_kill_50_cursors",
        docs=[{"_id": i} for i in range(100)],
        cursor_count=50,
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": list(ctx.cursors),
        },
        expected=lambda ctx: {
            "cursorsKilled": list(ctx.cursors),
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill all 50 cursors in a single batch",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_CORE_TESTS))
def test_killCursors_lifecycle(database_client, collection, test):
    """Test killCursors cursor lifecycle."""
    collection = test.prepare(database_client, collection)
    cursors = open_find_cursors(collection, test.cursor_count)
    ctx = CursorCommandContext.from_collection(collection, cursors=cursors)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_killCursors_aggregate_cursor(collection):
    """Test killCursors kills an aggregate cursor."""
    collection.insert_many([{"_id": i} for i in range(10)])
    res = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [], "cursor": {"batchSize": 1}},
    )
    cursor_id = res["cursor"]["id"]
    result = execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor from aggregate",
        raw_res=True,
    )


def test_killCursors_list_collections_cursor(database_client, collection):
    """Test killCursors kills a listCollections cursor."""
    db = database_client
    for i in range(10):
        db.create_collection(f"lc_kill_{i}")
    res = execute_command(
        collection,
        {"listCollections": 1, "cursor": {"batchSize": 1}},
    )
    cursor_id = res["cursor"]["id"]
    result = execute_command(
        collection,
        {"killCursors": "$cmd.listCollections", "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor from listCollections",
        raw_res=True,
    )


def test_killCursors_list_indexes_cursor(collection):
    """Test killCursors kills a listIndexes cursor."""
    collection.insert_many([{"_id": i} for i in range(10)])
    for i in range(10):
        collection.create_index([(f"field_{i}", 1)])
    res = execute_command(
        collection,
        {"listIndexes": collection.name, "cursor": {"batchSize": 1}},
    )
    cursor_id = res["cursor"]["id"]
    result = execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor from listIndexes",
        raw_res=True,
    )


def test_killCursors_view_cursor(database_client, collection):
    """Test killCursors kills a cursor opened against a view."""
    collection.insert_many([{"_id": i} for i in range(10)])
    view_name = collection.name + "_view"
    execute_command(
        collection,
        {"create": view_name, "viewOn": collection.name, "pipeline": []},
    )
    view = database_client[view_name]
    res = execute_command(view, {"find": view_name, "batchSize": 1})
    cursor_id = res["cursor"]["id"]
    result = execute_command(
        view,
        {"killCursors": view_name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor from a view",
        raw_res=True,
    )


def test_killCursors_timeseries_cursor(database_client, collection):
    """Test killCursors kills a cursor opened against a time-series collection."""
    ts_name = collection.name + "_ts"
    execute_command(
        collection,
        {"create": ts_name, "timeseries": {"timeField": "ts"}},
    )
    ts = database_client[ts_name]
    ts.insert_many(
        [{"ts": datetime.datetime(2024, 1, 1) + datetime.timedelta(minutes=i)} for i in range(20)]
    )
    res = execute_command(ts, {"find": ts_name, "batchSize": 1})
    cursor_id = res["cursor"]["id"]
    result = execute_command(
        ts,
        {"killCursors": ts_name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor from a time-series collection",
        raw_res=True,
    )


def test_killCursors_tailable_cursor(database_client):
    """Test killCursors kills a tailable cursor."""
    db = database_client
    db.create_collection("capped_for_kill", capped=True, size=100_000)
    capped = db["capped_for_kill"]
    capped.insert_many([{"_id": i} for i in range(10)])
    res = execute_command(
        capped,
        {"find": "capped_for_kill", "batchSize": 1, "tailable": True},
    )
    cursor_id = res["cursor"]["id"]
    result = execute_command(
        capped,
        {"killCursors": "capped_for_kill", "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor from tailable find",
        raw_res=True,
    )


# Property [Core Behavior - getMore After Kill]: after a cursor is
# killed, a getMore using that cursor ID produces CursorNotFound.
def test_killCursors_getmore_after_kill(collection):
    """Test getMore fails after cursor is killed."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)
    execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    getmore = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertFailureCode(
        getmore,
        CURSOR_NOT_FOUND_ERROR,
        msg="killCursors should kill cursor so getMore fails with CursorNotFound",
    )


# Property [Core Behavior - Sibling Cursors Unaffected]: killing one
# cursor does not affect sibling cursors from the same query.
def test_killCursors_sibling_unaffected(collection):
    """Test killing one cursor does not affect siblings."""
    collection.insert_many([{"_id": i} for i in range(10)])
    cursor_a, cursor_b = open_find_cursors(collection, 2)
    execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_a]},
    )
    getmore = execute_command(
        collection,
        {"getMore": cursor_b, "collection": collection.name},
    )
    assertSuccessPartial(getmore, {"ok": 1.0}, msg="killCursors should not affect sibling cursors")


# Property [cursors Element Type Rejection - Atomic Pre-Check]: if any
# element has a wrong type, the entire command fails and no cursors are
# killed, even valid cursors preceding the invalid element.
def test_killCursors_atomic_precheck_cursor_survives(collection):
    """Test valid cursors survive when type validation fails."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)
    execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id, "bad"]},
    )
    getmore = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertSuccessPartial(
        getmore,
        {"ok": 1.0},
        msg="killCursors should not kill valid cursors when type validation fails",
    )


# Property [Idempotency]: killing the same cursor twice reports it in
# cursorsKilled on the first attempt and cursorsNotFound on the second.
def test_killCursors_idempotency(collection):
    """Test killing the same cursor twice."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)

    execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )

    result = execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [cursor_id],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should report cursor in cursorsNotFound on second kill",
        raw_res=True,
    )


# Property [Mixed Cursor States]: when the cursors array contains a mix
# of active, already-killed, and non-existent IDs, each is correctly
# categorized into cursorsKilled or cursorsNotFound.
def test_killCursors_mixed_states(collection):
    """Test mixed active, killed, and non-existent cursor IDs."""
    collection.insert_many([{"_id": i} for i in range(10)])

    active_cursor, pre_killed_cursor = open_find_cursors(collection, 2)

    execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [pre_killed_cursor]},
    )

    nonexistent_cursor = Int64(999_999_999)

    result = execute_command(
        collection,
        {
            "killCursors": collection.name,
            "cursors": [active_cursor, pre_killed_cursor, nonexistent_cursor],
        },
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [active_cursor],
            "cursorsNotFound": [pre_killed_cursor, nonexistent_cursor],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should categorize active, killed, and non-existent IDs correctly",
        raw_res=True,
    )


# Property [Cursor Lifecycle After Metadata Changes]: a cursor remains
# killable after the source collection is dropped, renamed, recreated,
# or the source database is dropped.
def test_killCursors_after_drop_collection(database_client, collection):
    """Test cursor remains killable after source collection is dropped."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)

    database_client.drop_collection(collection.name)

    result = execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor after collection is dropped",
        raw_res=True,
    )


def test_killCursors_after_rename_collection(
    engine_client, database_client, collection, register_db_cleanup
):
    """Test cursor remains killable after source collection is renamed."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)

    renamed = collection.name + "_renamed"
    register_db_cleanup(f"{database_client.name}.{renamed}")
    engine_client.admin.command(
        {
            "renameCollection": f"{database_client.name}.{collection.name}",
            "to": f"{database_client.name}.{renamed}",
        }
    )

    result = execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor after collection is renamed",
        raw_res=True,
    )


def test_killCursors_after_recreate_collection(database_client, collection):
    """Test cursor remains killable after source collection is recreated."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)

    database_client.drop_collection(collection.name)
    database_client[collection.name].insert_one({"_id": 1, "new": True})

    result = execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor after collection is recreated",
        raw_res=True,
    )


def test_killCursors_after_drop_database(engine_client, database_client, collection):
    """Test cursor remains killable after source database is dropped."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)

    engine_client.drop_database(database_client.name)

    result = execute_command(
        collection,
        {"killCursors": collection.name, "cursors": [cursor_id]},
    )
    assertResult(
        result,
        expected={
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should kill cursor after database is dropped",
        raw_res=True,
    )


# Property [Cross-Connection Behavior]: a cursor created on one
# connection can be killed from a different connection to the same server.
def test_killCursors_cross_connection(connection_string, database_client, collection):
    """Test killing a cursor from a different connection."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1)

    second_client = fixtures.create_engine_client(connection_string, "second")
    try:
        second_coll = second_client[database_client.name][collection.name]
        result = execute_command(
            second_coll,
            {"killCursors": collection.name, "cursors": [cursor_id]},
        )
        assertResult(
            result,
            expected={
                "cursorsKilled": [cursor_id],
                "cursorsNotFound": [],
                "cursorsAlive": [],
                "cursorsUnknown": [],
                "ok": 1.0,
            },
            msg="killCursors should kill cursor from a different connection",
            raw_res=True,
        )
    finally:
        second_client.close()
