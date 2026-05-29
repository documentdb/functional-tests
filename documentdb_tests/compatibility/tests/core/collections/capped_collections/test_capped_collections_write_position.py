"""Tests for capped collection write position behaviors."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.target_collection import CappedCollection


# Property [Upsert Append]: upserts that create new documents append at the
# end of natural order.
@pytest.mark.collection_mgmt
def test_capped_upsert_append(database_client, collection):
    """Test that upserts append at end of natural order."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 5}, {"_id": 2}])
    coll.update_one({"_id": 1}, {"$set": {"v": "new"}}, upsert=True)
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 5}, {"_id": 2}, {"_id": 1}],
        msg="Upserted document should appear at the end of natural order",
    )


# Property [Update Position Preservation]: updates preserve a document's
# position in $natural order.
@pytest.mark.collection_mgmt
def test_capped_update_position(database_client, collection):
    """Test that updates preserve document position in natural order."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}, {"_id": 3, "x": "c"}])
    execute_command(
        coll, {"update": coll.name, "updates": [{"q": {"_id": 2}, "u": {"$set": {"x": "z" * 50}}}]}
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="Updates should preserve document position in natural order",
    )


# Property [Upsert Match No Eviction]: upserts that match an existing document
# act as normal updates with no eviction and no position change.
@pytest.mark.collection_mgmt
def test_capped_upsert_match(database_client, collection):
    """Test that upserts matching existing docs preserve order."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}, {"_id": 3, "x": "c"}])
    execute_command(
        coll,
        {
            "update": coll.name,
            "updates": [{"q": {"_id": 2}, "u": {"$set": {"x": "updated"}}, "upsert": True}],
        },
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="Upsert matching existing doc should not evict or change position",
    )


# Property [FindAndModify Update Position]: findAndModify with update preserves
# the document's position in natural order.
@pytest.mark.collection_mgmt
def test_capped_find_and_modify_position(database_client, collection):
    """Test that findAndModify update preserves document position."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}, {"_id": 3, "x": "c"}])
    execute_command(
        coll,
        {
            "findAndModify": coll.name,
            "query": {"_id": 2},
            "update": {"$set": {"x": "z" * 50}},
        },
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="findAndModify update should preserve document position in natural order",
    )


# Property [FindAndModify Remove Order]: findAndModify with remove preserves
# relative insertion order of remaining documents.
@pytest.mark.collection_mgmt
def test_capped_find_and_modify_remove_order(database_client, collection):
    """Test that findAndModify remove preserves relative order."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}])
    execute_command(coll, {"findAndModify": coll.name, "query": {"_id": 2}, "remove": True})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 3}, {"_id": 4}],
        msg="findAndModify remove should preserve relative insertion order",
    )


# Property [FindAndModify Upsert Append]: findAndModify with upsert that creates
# a new document appends it at the end of natural order.
@pytest.mark.collection_mgmt
def test_capped_find_and_modify_upsert_append(database_client, collection):
    """Test that findAndModify upsert appends at end of natural order."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1}, {"_id": 2}])
    execute_command(
        coll,
        {
            "findAndModify": coll.name,
            "query": {"_id": 5},
            "update": {"$set": {"x": "new"}},
            "upsert": True,
        },
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 5}],
        msg="findAndModify upsert should append new document at end of natural order",
    )


# Property [Multi Update Position Preservation]: update with multi:true
# preserves all affected documents' positions in natural order.
@pytest.mark.collection_mgmt
def test_capped_multi_update_position(database_client, collection):
    """Test that multi-update preserves all document positions."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many(
        [{"_id": 5, "x": 1}, {"_id": 3, "x": 2}, {"_id": 7, "x": 1}, {"_id": 1, "x": 1}]
    )
    execute_command(
        coll,
        {
            "update": coll.name,
            "updates": [{"q": {"x": 1}, "u": {"$set": {"x": 99}}, "multi": True}],
        },
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 5}, {"_id": 3}, {"_id": 7}, {"_id": 1}],
        msg="Multi-update should preserve all document positions in natural order",
    )


# Property [Replace Position Preservation]: a replacement-style update preserves
# the document's position in natural order.
@pytest.mark.collection_mgmt
def test_capped_replace_position(database_client, collection):
    """Test that replacement updates preserve document position."""
    coll = CappedCollection(size=100_000).resolve(database_client, collection)
    coll.insert_many([{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}, {"_id": 3, "x": "c"}])
    execute_command(
        coll,
        {"update": coll.name, "updates": [{"q": {"_id": 2}, "u": {"_id": 2, "y": "replaced"}}]},
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="Replacement update should preserve document position in natural order",
    )
