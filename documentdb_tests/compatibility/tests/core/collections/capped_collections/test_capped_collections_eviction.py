"""Tests for capped collection eviction behaviors."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CappedCollection


# Property [Eviction Order Preservation]: surviving documents maintain their
# relative insertion order after eviction has occurred.
@pytest.mark.collection_mgmt
def test_capped_eviction_order(database_client, collection):
    """Test insertion order preservation after eviction."""
    coll = CappedCollection(size=100_000, max=5).resolve(database_client, collection)
    for doc in [{"_id": i} for i in [10, 7, 3, 8, 1, 5, 9, 2, 6, 4]]:
        coll.insert_one(doc)
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 5}, {"_id": 9}, {"_id": 2}, {"_id": 6}, {"_id": 4}],
        msg="Surviving documents should maintain relative insertion order after eviction",
    )


# Property [Evicted _id Reuse]: after eviction removes a document, its _id
# value can be reused in a new insert.
@pytest.mark.collection_mgmt
def test_capped_duplicate_id_reuse(database_client, collection):
    """Test that evicted _id values can be reused."""
    coll = CappedCollection(size=100_000, max=2).resolve(database_client, collection)
    for doc in [{"_id": 1}, {"_id": 2}, {"_id": 3}]:
        coll.insert_one(doc)
    # _id:1 was evicted (max=2 keeps only last 2). Reinsert it.
    coll.insert_one({"_id": 1})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 3}, {"_id": 1}],
        msg="An evicted _id value should be reusable in a new insert",
    )


# Property [Eviction Removes Index Entries]: evicted documents are no longer
# findable via secondary indexes.
@pytest.mark.collection_mgmt
def test_capped_eviction_index_cleanup(database_client, collection):
    """Test that eviction removes entries from secondary indexes."""
    coll = CappedCollection(size=100_000, max=3).resolve(database_client, collection)
    coll.create_index("x")
    coll.insert_many([{"_id": 1, "x": "findme"}, {"_id": 2, "x": "b"}, {"_id": 3, "x": "c"}])
    # Trigger eviction by inserting beyond max.
    coll.insert_one({"_id": 4, "x": "d"})
    # The evicted document should no longer be findable via the index.
    result = execute_command(
        coll, {"find": coll.name, "filter": {"x": "findme"}, "projection": {"_id": 1}}
    )
    assertSuccess(result, [], msg="Evicted documents should not be findable via secondary index")


# Property [Size-Based Eviction]: when the total data size exceeds the byte
# size cap, the oldest documents are evicted to make room.
@pytest.mark.collection_mgmt
def test_capped_size_based_eviction(database_client, collection):
    """Test that size-based eviction removes oldest documents."""
    coll = CappedCollection(size=4096).resolve(database_client, collection)
    for i in range(50):
        coll.insert_one({"_id": i, "data": "x" * 500})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})

    def validate_size_eviction(r):
        ids = [d["_id"] for d in r["cursor"]["firstBatch"]]
        # Eviction occurred, most recent survives, in insertion order
        return len(ids) < 50 and ids[-1] == 49 and ids == list(range(ids[0], ids[-1] + 1))

    assertSuccess(
        result,
        True,
        msg="Size-based eviction should remove oldest docs, preserving insertion order",
        raw_res=True,
        transform=validate_size_eviction,
    )


# Property [Dual Constraint Max First]: when both size and max are specified
# and max is the tighter constraint, eviction is triggered by max.
@pytest.mark.collection_mgmt
def test_capped_dual_constraint_max_triggers(database_client, collection):
    """Test that max triggers eviction when it is the tighter constraint."""
    coll = CappedCollection(size=1_000_000, max=3).resolve(database_client, collection)
    coll.insert_many([{"_id": i} for i in range(7)])
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 4}, {"_id": 5}, {"_id": 6}],
        msg="max should trigger eviction when it is the tighter constraint",
    )


# Property [Dual Constraint Size First]: when both size and max are specified
# and size is the tighter constraint, eviction is triggered by size.
@pytest.mark.collection_mgmt
def test_capped_dual_constraint_size_triggers(database_client, collection):
    """Test that size triggers eviction when it is the tighter constraint."""
    coll = CappedCollection(size=4096, max=1000).resolve(database_client, collection)
    for i in range(50):
        coll.insert_one({"_id": i, "data": "x" * 500})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})

    def validate_size_triggers_first(r):
        ids = [d["_id"] for d in r["cursor"]["firstBatch"]]
        # Size triggered (count well below max=1000), most recent survives, in order
        return len(ids) < 50 and ids[-1] == 49 and ids == list(range(ids[0], ids[-1] + 1))

    assertSuccess(
        result,
        True,
        msg="Size should trigger eviction before max is reached",
        raw_res=True,
        transform=validate_size_triggers_first,
    )


# Property [Batch Insert Eviction]: a single insertMany that exceeds the max
# document limit evicts oldest documents, keeping only the last max documents.
@pytest.mark.collection_mgmt
def test_capped_batch_insert_eviction(database_client, collection):
    """Test eviction during a single insertMany call."""
    coll = CappedCollection(size=100_000, max=5).resolve(database_client, collection)
    coll.insert_many([{"_id": i} for i in range(10)])
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 5}, {"_id": 6}, {"_id": 7}, {"_id": 8}, {"_id": 9}],
        msg="Batch insert should evict oldest documents when max is exceeded",
    )


# Property [Count Reflects Eviction]: the count command returns only the
# number of surviving documents after eviction.
@pytest.mark.collection_mgmt
def test_capped_count_reflects_eviction(database_client, collection):
    """Test that count reflects eviction."""
    coll = CappedCollection(size=100_000, max=3).resolve(database_client, collection)
    coll.insert_many([{"_id": i} for i in range(10)])
    result = execute_command(coll, {"count": coll.name})
    assertProperties(
        result,
        {"n": Eq(3)},
        msg="Count should reflect only surviving documents after eviction",
        raw_res=True,
    )


# Property [CollMod Max No Immediate Eviction]: reducing cappedMax via collMod
# does not immediately evict existing documents.
@pytest.mark.collection_mgmt
def test_capped_collmod_max_no_immediate_eviction(database_client, collection):
    """Test that reducing cappedMax does not immediately evict documents."""
    coll = CappedCollection(size=1_048_576, max=10).resolve(database_client, collection)
    coll.insert_many([{"_id": i} for i in range(1, 6)])
    execute_command(coll, {"collMod": coll.name, "cappedMax": 3})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        msg="Reducing cappedMax should not immediately evict existing documents",
    )


# Property [CollMod Max Deferred Eviction]: after reducing cappedMax via collMod,
# the next insert triggers eviction down to the new limit.
@pytest.mark.collection_mgmt
def test_capped_collmod_max_deferred_eviction(database_client, collection):
    """Test that next insert after cappedMax reduction triggers eviction."""
    coll = CappedCollection(size=1_048_576, max=10).resolve(database_client, collection)
    coll.insert_many([{"_id": i} for i in range(1, 6)])
    execute_command(coll, {"collMod": coll.name, "cappedMax": 3})
    coll.insert_one({"_id": 6})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 4}, {"_id": 5}, {"_id": 6}],
        msg="Next insert after cappedMax reduction should trigger eviction to new limit",
    )


# Property [CollMod Size No Immediate Eviction]: reducing cappedSize via collMod
# does not immediately evict existing documents.
@pytest.mark.collection_mgmt
def test_capped_collmod_size_no_immediate_eviction(database_client, collection):
    """Test that reducing cappedSize does not immediately evict documents."""
    coll = CappedCollection(size=1_048_576).resolve(database_client, collection)
    for i in range(10):
        coll.insert_one({"_id": i, "data": "x" * 500})
    execute_command(coll, {"collMod": coll.name, "cappedSize": 4096})
    result = execute_command(coll, {"count": coll.name})
    assertProperties(
        result,
        {"n": Eq(10)},
        msg="Reducing cappedSize should not immediately evict existing documents",
        raw_res=True,
    )


# Property [CollMod Size Deferred Eviction]: after reducing cappedSize via
# collMod, the next insert triggers eviction based on the new size limit.
@pytest.mark.collection_mgmt
def test_capped_collmod_size_deferred_eviction(database_client, collection):
    """Test that next insert after cappedSize reduction triggers eviction."""
    coll = CappedCollection(size=1_048_576).resolve(database_client, collection)
    for i in range(10):
        coll.insert_one({"_id": i, "data": "x" * 500})
    execute_command(coll, {"collMod": coll.name, "cappedSize": 4096})
    coll.insert_one({"_id": 10, "data": "x" * 500})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})

    def validate_deferred_size_eviction(r):
        ids = [d["_id"] for d in r["cursor"]["firstBatch"]]
        # Eviction occurred, most recent survives, in insertion order
        return len(ids) < 11 and ids[-1] == 10 and ids == list(range(ids[0], ids[-1] + 1))

    assertSuccess(
        result,
        True,
        msg="Next insert after cappedSize reduction should trigger eviction to new limit",
        raw_res=True,
        transform=validate_deferred_size_eviction,
    )


# Property [Oversize Document Accepted]: a single document larger than the
# declared size cap is accepted.
@pytest.mark.collection_mgmt
def test_capped_oversize_document_accepted(database_client, collection):
    """Test that a document larger than the size cap is accepted."""
    coll = CappedCollection(size=4096).resolve(database_client, collection)
    coll.insert_one({"_id": 1, "data": "x" * 10000})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1}],
        msg="A document larger than the size cap should be accepted",
    )


# Property [Oversize Document Evicted]: after accepting an oversize document,
# subsequent inserts evict it following normal oldest-first eviction.
@pytest.mark.collection_mgmt
def test_capped_oversize_document_evicted(database_client, collection):
    """Test that an oversize document is evicted by subsequent inserts."""
    coll = CappedCollection(size=4096).resolve(database_client, collection)
    coll.insert_one({"_id": 1, "data": "x" * 10000})
    coll.insert_one({"_id": 2, "data": "y" * 50})
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 2}],
        msg="Oversize document should be evicted by subsequent inserts",
    )
