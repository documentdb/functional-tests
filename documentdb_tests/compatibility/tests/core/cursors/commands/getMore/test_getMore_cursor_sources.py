"""Tests for getMore against cursors from different source commands.

find cursors are exercised exhaustively across the other getMore test files.
This file holds one representative per other cursor source (aggregate, view,
time-series, listCollections, listIndexes), confirming each source's cursor
reaches the same getMore handling.
"""

from __future__ import annotations

import datetime

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len


# Property [Aggregate Cursor Source]: getMore retrieves a subsequent batch from
# an aggregate cursor.
def test_getMore_aggregate_cursor(collection):
    """Test getMore returns a subsequent batch from an aggregate cursor."""
    collection.insert_many([{"_id": i} for i in range(10)])
    agg_result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [], "cursor": {"batchSize": 2}},
    )
    cursor_id = agg_result["cursor"]["id"]
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 3},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3)}},
        msg="getMore should return next batch from an aggregate cursor",
        raw_res=True,
    )


# Property [View Cursor Source]: getMore retrieves a subsequent batch from a
# cursor over a view, addressed by the view name.
def test_getMore_view_cursor(collection):
    """Test getMore returns a subsequent batch from a view cursor."""
    collection.insert_many([{"_id": i} for i in range(5)])
    view_name = f"{collection.name}_view"
    execute_command(collection, {"create": view_name, "viewOn": collection.name, "pipeline": []})
    find_result = execute_command(collection, {"find": view_name, "batchSize": 2})
    cursor_id = find_result["cursor"]["id"]
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": view_name},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3)}},
        msg="getMore should return next batch from a view cursor",
        raw_res=True,
    )


# Property [Time-Series Cursor Source]: getMore retrieves a subsequent batch
# from a cursor over a time-series collection.
def test_getMore_timeseries_cursor(collection):
    """Test getMore returns a subsequent batch from a time-series cursor."""
    ts_name = f"{collection.name}_ts"
    execute_command(collection, {"create": ts_name, "timeseries": {"timeField": "ts"}})
    execute_command(
        collection,
        {
            "insert": ts_name,
            "documents": [
                {"ts": datetime.datetime(2024, 1, 1) + datetime.timedelta(minutes=i)}
                for i in range(20)
            ],
        },
    )
    find_result = execute_command(collection, {"find": ts_name, "batchSize": 2})
    cursor_id = find_result["cursor"]["id"]
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": ts_name, "batchSize": 3},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3)}},
        msg="getMore should return next batch from a time-series cursor",
        raw_res=True,
    )


# Property [listCollections Cursor Source]: getMore retrieves a subsequent
# batch from a listCollections cursor, addressed by $cmd.listCollections.
def test_getMore_list_collections_cursor(collection):
    """Test getMore succeeds for a listCollections cursor."""
    for i in range(5):
        execute_command(collection, {"create": f"{collection.name}_lc_{i}"})
    list_result = execute_command(
        collection,
        {"listCollections": 1, "cursor": {"batchSize": 1}},
    )
    cursor_id = list_result["cursor"]["id"]
    if cursor_id == 0:
        pytest.skip("listCollections returned all results in first batch")
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": "$cmd.listCollections"},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg="getMore should succeed for a listCollections cursor",
        raw_res=True,
    )


# Property [listIndexes Cursor Source]: getMore retrieves a subsequent batch
# from a listIndexes cursor, addressed by the collection name.
def test_getMore_list_indexes_cursor(collection):
    """Test getMore succeeds for a listIndexes cursor."""
    collection.insert_many([{"_id": i} for i in range(3)])
    for i in range(10):
        execute_command(
            collection,
            {
                "createIndexes": collection.name,
                "indexes": [{"key": {f"f{i}": 1}, "name": f"idx_{i}"}],
            },
        )
    list_result = execute_command(
        collection,
        {"listIndexes": collection.name, "cursor": {"batchSize": 1}},
    )
    cursor_id = list_result["cursor"]["id"]
    if cursor_id == 0:
        pytest.skip("listIndexes returned all results in first batch")
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg="getMore should succeed for a listIndexes cursor",
        raw_res=True,
    )
