"""Tests for getMore batch retrieval behavior."""

from __future__ import annotations

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    open_cursor,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Gte, Len
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_constants import INT64_ZERO


# Property [Batch Retrieval]: getMore returns the next batch of documents from a cursor.
def test_getMore_batch_from_find(collection):
    """Test getMore returns subsequent batches from a find cursor."""
    collection.insert_many([{"_id": i, "v": i} for i in range(10)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=3)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 4},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "cursor": {"nextBatch": Eq([{"_id": i, "v": i} for i in range(3, 7)])},
        },
        msg="getMore should return next 4 documents from find cursor",
        raw_res=True,
    )


# Property [batchSize Zero Tailable]: getMore with batchSize=0 on a tailable
# cursor returns available documents and keeps the cursor open.
def test_getMore_batch_size_zero_tailable_keeps_open(collection):
    """Test getMore with batchSize=0 on tailable cursor keeps it open."""
    capped = CappedCollection().resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(5)])
    cursor_id = open_cursor(capped, {"tailable": True, "batchSize": 2})
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": capped.name, "batchSize": 0},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3), "id": Gte(1)}},
        msg="getMore batchSize=0 on tailable cursor should return docs and keep open",
        raw_res=True,
    )


# Property [batchSize Independence]: each getMore call applies its own batchSize
# independent of the find batchSize and prior calls.
def test_getMore_batch_size_independent(collection):
    """Test each getMore call sets its own batchSize independently."""
    docs = [{"_id": i, "v": i} for i in range(10)]
    collection.insert_many(docs)
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    result1 = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 3},
    )
    cursor_id = result1["cursor"]["id"]
    result2 = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 5},
    )
    assertResult(
        result2,
        expected={
            "ok": Eq(1.0),
            "cursor": {"nextBatch": Eq([{"_id": i, "v": i} for i in range(5, 10)])},
        },
        msg="Second getMore should return 5 documents independently of find batchSize",
        raw_res=True,
    )


# Property [Limit Cap]: the originating find's limit caps the total number of
# documents returned across getMore calls.
def test_getMore_find_limit_caps_total(collection):
    """Test the originating find's limit caps total documents across getMore calls."""
    docs = [{"_id": i, "v": i} for i in range(10)]
    collection.insert_many(docs)
    find_result = execute_command(collection, {"find": collection.name, "batchSize": 2, "limit": 5})
    cursor_id = find_result["cursor"]["id"]
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 10},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3), "id": Eq(INT64_ZERO)}},
        msg="getMore should return only 3 more documents to respect limit=5",
        raw_res=True,
    )


# Property [Cursor Independence]: separate cursors on the same collection
# maintain independent iteration positions.
def test_getMore_independent_cursors(collection):
    """Test two cursors on the same collection maintain independent positions."""
    docs = [{"_id": i, "v": i} for i in range(10)]
    collection.insert_many(docs)
    (cursor_a,) = open_find_cursors(collection, 1, batch_size=3)
    (cursor_b,) = open_find_cursors(collection, 1, batch_size=5)
    result_a = execute_command(
        collection,
        {"getMore": cursor_a, "collection": collection.name, "batchSize": 2},
    )
    result_b = execute_command(
        collection,
        {"getMore": cursor_b, "collection": collection.name, "batchSize": 2},
    )
    # Cursor A started at position 3, cursor B started at position 5.
    combined = {
        "a": result_a["cursor"]["nextBatch"],
        "b": result_b["cursor"]["nextBatch"],
    }
    assertResult(
        combined,
        expected={
            "a": Eq([{"_id": 3, "v": 3}, {"_id": 4, "v": 4}]),
            "b": Eq([{"_id": 5, "v": 5}, {"_id": 6, "v": 6}]),
        },
        msg="Two cursors should maintain independent positions",
        raw_res=True,
    )
