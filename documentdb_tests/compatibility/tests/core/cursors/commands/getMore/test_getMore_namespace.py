"""Tests for getMore namespace matching."""

from __future__ import annotations

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNAUTHORIZED_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len


# Property [Namespace Match Success]: getMore succeeds when the collection
# parameter exactly matches the find cursor's bound namespace.
def test_getMore_namespace_match_find(collection):
    """Test getMore succeeds with exact collection name match for find cursor."""
    collection.insert_many([{"_id": i} for i in range(5)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "cursor": {"nextBatch": Len(3)}},
        msg="getMore should succeed when collection matches find cursor namespace",
        raw_res=True,
    )


# Property [Namespace Case Sensitivity]: getMore requires an exact
# case-sensitive match for the collection name.
def test_getMore_namespace_case_sensitive(collection):
    """Test getMore requires exact case-sensitive match for collection name."""
    collection.insert_many([{"_id": i} for i in range(5)])
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name.upper()},
    )
    assertResult(
        result,
        error_code=UNAUTHORIZED_ERROR,
        msg="getMore should reject uppercase variant of actual collection name",
        raw_res=True,
    )


# Property [Namespace View Binding]: a view cursor is bound to the view name;
# getMore addressed to the underlying collection is rejected.
def test_getMore_namespace_view_bound_to_view_name(collection):
    """Test view cursors are bound to the view name, not the underlying collection."""
    collection.insert_many([{"_id": i} for i in range(5)])
    view_name = f"{collection.name}_view"
    execute_command(collection, {"create": view_name, "viewOn": collection.name, "pipeline": []})
    find_result = execute_command(collection, {"find": view_name, "batchSize": 2})
    cursor_id = find_result["cursor"]["id"]
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        error_code=UNAUTHORIZED_ERROR,
        msg="getMore should reject underlying collection name for a view cursor",
        raw_res=True,
    )
