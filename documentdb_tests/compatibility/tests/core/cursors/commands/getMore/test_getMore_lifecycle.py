"""Tests for getMore cursor lifecycle behavior."""

from __future__ import annotations

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    open_cursor,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    CURSOR_NOT_FOUND_ERROR,
    QUERY_PLAN_KILLED_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Gte
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_constants import INT64_ZERO


# Property [Cursor Lifecycle - Exhausted]: getMore on an exhausted cursor
# produces CURSOR_NOT_FOUND_ERROR.
def test_getMore_exhausted_cursor_error(collection):
    """Test getMore on an exhausted cursor produces CursorNotFound."""
    collection.insert_many([{"_id": i} for i in range(4)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 10},
    )
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        error_code=CURSOR_NOT_FOUND_ERROR,
        msg="getMore should produce CursorNotFound on an exhausted cursor",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Killed]: getMore on a killed cursor produces
# CURSOR_NOT_FOUND_ERROR.
def test_getMore_killed_cursor_error(collection):
    """Test getMore on a killed cursor produces CursorNotFound."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    execute_command(collection, {"killCursors": collection.name, "cursors": [cursor_id]})
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        error_code=CURSOR_NOT_FOUND_ERROR,
        msg="getMore should produce CursorNotFound on a killed cursor",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Collection Drop]: getMore after the collection
# is dropped produces QUERY_PLAN_KILLED_ERROR.
def test_getMore_after_collection_drop(collection):
    """Test getMore after collection drop produces QueryPlanKilled."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    collection.drop()
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        error_code=QUERY_PLAN_KILLED_ERROR,
        msg="getMore should produce QueryPlanKilled after collection is dropped",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Drop and Recreate]: getMore after the collection
# is dropped and recreated still produces QUERY_PLAN_KILLED_ERROR.
def test_getMore_after_drop_and_recreate(collection):
    """Test getMore after drop and recreate still produces QueryPlanKilled."""
    collection.insert_many([{"_id": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    collection.drop()
    collection.insert_many([{"_id": i, "new": True} for i in range(5)])
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        error_code=QUERY_PLAN_KILLED_ERROR,
        msg="getMore should produce QueryPlanKilled after drop and recreate",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Find batchSize Zero]: batchSize=0 on the
# originating find establishes a cursor without returning documents, and
# subsequent getMore returns documents.
def test_getMore_find_batch_size_zero(collection):
    """Test getMore returns documents after find with batchSize=0."""
    collection.insert_many([{"_id": i} for i in range(5)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=0)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 3},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Eq([{"_id": 0}, {"_id": 1}, {"_id": 2}])}},
        msg="getMore should return documents after find with batchSize=0",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Tailable Stays Open]: a tailable cursor stays
# open and returns an empty batch when it reaches the end of data.
def test_getMore_tailable_stays_open_at_end(collection):
    """Test tailable cursor stays open at end of data."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 10})
    gm = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 0},
    )
    assertResult(
        gm,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Eq([]), "id": Gte(1)}},
        msg="getMore on tailable cursor at end of data should return empty and stay open",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Tailable New Inserts]: a tailable cursor returns
# documents inserted after it reached the end of data.
def test_getMore_tailable_sees_new_inserts(collection):
    """Test tailable cursor sees new inserts on subsequent getMore."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "awaitData": True, "batchSize": 10})
    # Insert new data after find consumed all existing docs in firstBatch.
    capped.insert_one({"_id": 99, "new": True})
    gm = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 100},
    )
    assertResult(
        gm,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Eq([{"_id": 99, "new": True}])}},
        msg="getMore on tailable cursor should see new inserts",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Delete Visibility]: a find cursor does not
# return documents deleted before it reaches them; documents already returned
# are unaffected.
def test_getMore_deleted_docs_still_visible(collection):
    """Test getMore skips documents deleted before the cursor reaches them."""
    collection.insert_many([{"_id": i, "v": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    # firstBatch returned _id 0,1; cursor is positioned at _id 2.
    collection.delete_many({"_id": {"$gte": 5}})
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 10},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "id": Eq(INT64_ZERO),
                "nextBatch": Eq([{"_id": 2, "v": 2}, {"_id": 3, "v": 3}, {"_id": 4, "v": 4}]),
            },
        },
        msg="getMore should skip documents deleted before the cursor reached them",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Insert Visibility]: documents inserted during
# iteration are visible in subsequent getMore calls.
def test_getMore_new_inserts_visible(collection):
    """Test new documents inserted during iteration are visible in getMore."""
    collection.insert_many([{"_id": i} for i in range(5)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    collection.insert_many([{"_id": 100 + i, "new": True} for i in range(3)])
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 100},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "nextBatch": Eq(
                    [
                        {"_id": 2},
                        {"_id": 3},
                        {"_id": 4},
                        {"_id": 100, "new": True},
                        {"_id": 101, "new": True},
                        {"_id": 102, "new": True},
                    ]
                )
            },
        },
        msg="getMore should see documents inserted during iteration",
        raw_res=True,
    )


# Property [Cursor Lifecycle - Update Visibility]: a find cursor returns the
# updated value of a document modified before the cursor reaches it.
def test_getMore_updated_docs_show_new_value(collection):
    """Test getMore returns the new value of a document updated before it is reached."""
    collection.insert_many([{"_id": i, "v": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    # firstBatch returned _id 0,1; cursor is positioned at _id 2.
    collection.update_one({"_id": 4}, {"$set": {"v": 999}})
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 10},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "id": Eq(INT64_ZERO),
                "nextBatch": Eq([{"_id": i, "v": 999 if i == 4 else i} for i in range(2, 10)]),
            },
        },
        msg="getMore should return the updated value of a document modified before it is reached",
        raw_res=True,
    )
