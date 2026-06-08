"""Tests for capped collection delete behaviors."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CappedCollection


# Property [Delete Order Preservation]: after deletes, remaining documents
# maintain their relative insertion order.
@pytest.mark.collection_mgmt
def test_capped_delete_order(database_client, collection):
    """Test that deletes preserve relative insertion order."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}])
    execute_command(coll, {"delete": coll.name, "deletes": [{"q": {"_id": 3}, "limit": 1}]})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 4}, {"_id": 5}],
        msg="Remaining documents should maintain relative insertion order after delete",
    )


# Property [Delete Insert Append]: after deletes, new inserts append at the
# end of natural order and deleted positions are not reused.
@pytest.mark.collection_mgmt
def test_capped_delete_insert_append(database_client, collection):
    """Test that new inserts after delete append at the end."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    execute_command(coll, {"delete": coll.name, "deletes": [{"q": {"_id": 2}, "limit": 1}]})
    coll.insert_one({"_id": 4})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 3}, {"_id": 4}],
        msg="New inserts after delete should append at the end of natural order",
    )


# Property [Delete Preserves Capped]: the collection remains capped after any
# delete operation.
@pytest.mark.collection_mgmt
def test_capped_delete_remains_capped(database_client, collection):
    """Test that the collection remains capped after deletes."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    execute_command(coll, {"delete": coll.name, "deletes": [{"q": {}, "limit": 0}]})
    result = execute_command(coll, {"collStats": coll.name})
    assertProperties(
        result,
        {"capped": Eq(True)},
        msg="Collection should remain capped after delete",
        raw_res=True,
    )


# Property [Delete Natural Hint Forward]: $natural:1 hint in a delete targets
# the oldest document.
@pytest.mark.collection_mgmt
def test_capped_delete_hint_natural_forward(database_client, collection):
    """Test $natural:1 hint targets the oldest document for deletion."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}])
    execute_command(
        coll, {"delete": coll.name, "deletes": [{"q": {}, "limit": 1, "hint": {"$natural": 1}}]}
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        msg="$natural:1 hint should target the oldest document for deletion",
    )


# Property [Delete Natural Hint Reverse]: $natural:-1 hint in a delete targets
# the newest document.
@pytest.mark.collection_mgmt
def test_capped_delete_hint_natural_reverse(database_client, collection):
    """Test $natural:-1 hint targets the newest document for deletion."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}])
    execute_command(
        coll, {"delete": coll.name, "deletes": [{"q": {}, "limit": 1, "hint": {"$natural": -1}}]}
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}],
        msg="$natural:-1 hint should target the newest document for deletion",
    )
