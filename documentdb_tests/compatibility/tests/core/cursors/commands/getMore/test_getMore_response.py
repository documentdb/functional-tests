"""Tests for getMore response structure."""

from __future__ import annotations

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, IsType
from documentdb_tests.framework.test_constants import INT64_ZERO


# Property [Response Structure]: the getMore response contains ok (double),
# cursor.id (long), cursor.ns (string), and cursor.nextBatch (array).
def test_getMore_response_structure(collection):
    """Test getMore response structure and field types."""
    collection.insert_many([{"_id": i} for i in range(5)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 2},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "id": IsType("long"),
                "ns": IsType("string"),
                "nextBatch": IsType("array"),
            },
        },
        msg=(
            "getMore response should contain ok, cursor.id,"
            " cursor.ns, and cursor.nextBatch with correct types"
        ),
        raw_res=True,
    )


# Property [Exhausted Cursor Response]: when the cursor is exhausted,
# cursor.id is 0 and nextBatch is empty.
def test_getMore_exhausted_cursor_response(collection):
    """Test getMore response when cursor is exhausted."""
    collection.insert_many([{"_id": i} for i in range(4)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    gm1 = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 2},
    )
    cursor_id2 = gm1["cursor"]["id"]
    result = execute_command(
        collection,
        {"getMore": cursor_id2, "collection": collection.name, "batchSize": 2},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "cursor": {"id": Eq(INT64_ZERO), "nextBatch": Eq([])},
        },
        msg="getMore should return cursor.id=0 and empty nextBatch when exhausted",
        raw_res=True,
    )
