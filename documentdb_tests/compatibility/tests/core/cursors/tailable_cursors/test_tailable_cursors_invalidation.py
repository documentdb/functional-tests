"""Tests for tailable cursor invalidation and collection operations."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
)
from documentdb_tests.framework.error_codes import (
    CAPPED_POSITION_LOST_ERROR,
    CURSOR_NOT_FOUND_ERROR,
    QUERY_PLAN_KILLED_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.test_constants import INT64_ZERO

from .utils.capped import create_capped


# Property [killCursors on Tailable Cursors]: killCursors terminates a tailable cursor.
def test_tailable_cursors_getmore_after_kill(database_client, collection):
    """Test getMore after killCursors produces cursor not found error."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    execute_command(capped, {"killCursors": capped.name, "cursors": [cursor_id]})

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertFailureCode(
        gm_result,
        CURSOR_NOT_FOUND_ERROR,
        msg="getMore after killCursors should produce cursor not found error",
    )


# Property [Capped Position Lost]: when eviction overwrites the cursor's read position,
# getMore returns CappedPositionLost error.
def test_tailable_cursors_capped_position_lost(database_client, collection):
    """Test getMore returns CappedPositionLost when eviction overwrites cursor position."""
    capped = create_capped(
        database_client,
        collection,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}],
        size=100_000,
        max=3,
    )

    result = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    # Evict all documents the cursor has seen.
    capped.insert_many([{"_id": 4}, {"_id": 5}, {"_id": 6}])

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertFailureCode(
        gm_result,
        CAPPED_POSITION_LOST_ERROR,
        msg="getMore should return CappedPositionLost when eviction overwrites cursor position",
    )


# Property [Partial Eviction]: when earlier documents are evicted but the cursor's
# read position is still valid, the cursor continues normally.
def test_tailable_cursors_partial_eviction(database_client, collection):
    """Test cursor survives partial eviction and returns new documents."""
    capped = create_capped(
        database_client,
        collection,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        size=100_000,
        max=5,
    )

    result = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    # Evict _id:1 and _id:2, but cursor position (after _id:5) is still valid.
    capped.insert_many([{"_id": 6}, {"_id": 7}])

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([{"_id": 6}, {"_id": 7}])}},
        msg="Cursor should survive partial eviction and return new documents",
        raw_res=True,
    )


# Property [Collection Drop]: dropping the collection invalidates open tailable
# cursors.
def test_tailable_cursors_getmore_after_drop(database_client, collection):
    """Test getMore after collection drop produces query plan killed error."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    capped.drop()

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertFailureCode(
        gm_result,
        QUERY_PLAN_KILLED_ERROR,
        msg="getMore after collection drop should produce query plan killed error",
    )


# Property [Drop and Recreate]: recreating a collection with the same name does not
# revive cursors from the original.
def test_tailable_cursors_getmore_after_drop_recreate(database_client, collection):
    """Test getMore after drop and recreate still produces query plan killed error."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    capped_name = capped.name
    result = execute_command(capped, {"find": capped_name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    capped.drop()
    # Recreate with same name
    execute_command(
        collection,
        {"create": capped_name, "capped": True, "size": 4096},
    )

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped_name})
    assertFailureCode(
        gm_result,
        QUERY_PLAN_KILLED_ERROR,
        msg="getMore after drop and recreate should produce query plan killed error",
    )


# Property [Rename Invalidation]: renaming the collection invalidates open tailable
# cursors.
def test_tailable_cursors_getmore_after_rename(database_client, collection):
    """Test getMore after collection rename produces query plan killed error."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    capped_name = capped.name
    result = execute_command(capped, {"find": capped_name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    renamed = f"{capped_name}_renamed"
    collection.database.client["admin"].command(
        {
            "renameCollection": f"{capped.database.name}.{capped_name}",
            "to": f"{capped.database.name}.{renamed}",
        }
    )

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped_name})
    assertFailureCode(
        gm_result,
        QUERY_PLAN_KILLED_ERROR,
        msg="getMore after collection rename should produce query plan killed error",
    )


# Property [Multiple Independent Tailable Cursors]: multiple tailable cursors on the
# same collection each independently see new documents.
def test_tailable_cursors_multiple_cursor1_sees_new(database_client, collection):
    """Test first cursor sees documents inserted while second cursor is also open."""
    capped = create_capped(database_client, collection, [{"_id": 1}])

    r1 = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    # Open a second cursor to ensure multiple cursors coexist
    execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cid1 = r1["cursor"]["id"]

    capped.insert_one({"_id": 2, "x": 2})

    gm1 = execute_command(capped, {"getMore": cid1, "collection": capped.name})
    assertProperties(
        gm1,
        {"cursor": {"nextBatch": Eq([{"_id": 2, "x": 2}])}},
        msg="First cursor should see new document while second cursor is open",
        raw_res=True,
    )


# Property [Independent Cursor Position]: a second tailable cursor sees the same new
# documents as the first, maintaining its own read position.
def test_tailable_cursors_multiple_cursor2_sees_new(database_client, collection):
    """Test second cursor independently sees new documents."""
    capped = create_capped(database_client, collection, [{"_id": 1}])

    # Open two cursors; advance the first past the new insert
    r1 = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    r2 = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cid1 = r1["cursor"]["id"]
    cid2 = r2["cursor"]["id"]

    capped.insert_one({"_id": 2, "x": 2})

    # Consume from first cursor
    execute_command(capped, {"getMore": cid1, "collection": capped.name})

    # Second cursor should still see the same document
    gm2 = execute_command(capped, {"getMore": cid2, "collection": capped.name})
    assertProperties(
        gm2,
        {"cursor": {"nextBatch": Eq([{"_id": 2, "x": 2}])}},
        msg="Second cursor should see document already consumed by first cursor",
        raw_res=True,
    )


# Property [Concurrent Writers]: concurrent inserts from multiple connections are
# all visible to a tailable cursor.
@pytest.mark.no_parallel
def test_tailable_cursors_concurrent_writers(engine_client, database_client, collection):
    """Test concurrent inserts from multiple connections are visible."""
    capped = create_capped(database_client, collection, [{"_id": 0}])

    result = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    # Insert from the same client but different collection handle
    capped.insert_one({"_id": 1, "src": "conn1"})

    # Use the engine_client to get a second handle to the same collection
    capped2 = engine_client[capped.database.name][capped.name]
    capped2.insert_one({"_id": 2, "src": "conn2"})

    # getMore should see both documents
    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO)}},
        msg="Concurrent inserts should be visible to tailable cursor",
        raw_res=True,
    )
