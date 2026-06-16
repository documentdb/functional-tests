"""Tests for top command core behavior.

Validates that counters reflect operations and cross-lock consistency invariants hold.
"""

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Gt, Gte

pytestmark = pytest.mark.admin


# ---------- Counter Behavior — Statistics Reflect Operations ----------


def test_top_insert_increments_insert_count(collection):
    """Test that inserting documents increments the insert count."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data,
        {"insert.count": Gte(1)},
        msg="insert.count should be >= 1 after inserts",
        raw_res=True,
    )


def test_top_insert_increments_writeLock_count(collection):
    """Test that inserting documents increments the writeLock count."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data,
        {"writeLock.count": Gte(1)},
        msg="writeLock.count should be >= 1 after inserts",
        raw_res=True,
    )


def test_top_query_increments_queries_count(collection):
    """Test that running a find query increments the queries count."""
    collection.insert_one({"_id": 1})
    list(collection.find())
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data, {"queries.count": Gte(1)}, msg="queries.count should be >= 1", raw_res=True
    )


def test_top_query_increments_readLock_count(collection):
    """Test that running a find query increments the readLock count."""
    collection.insert_one({"_id": 1})
    list(collection.find())
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data, {"readLock.count": Gte(1)}, msg="readLock.count should be >= 1", raw_res=True
    )


def test_top_update_increments_update_count(collection):
    """Test that running an update increments the update count."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.update_one({"_id": 1}, {"$set": {"a": 2}})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data, {"update.count": Gte(1)}, msg="update.count should be >= 1", raw_res=True
    )


def test_top_update_increments_writeLock_count(collection):
    """Test that running an update increments the writeLock count."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.update_one({"_id": 1}, {"$set": {"a": 2}})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data,
        {"writeLock.count": Gte(1)},
        msg="writeLock.count should be >= 1 after update",
        raw_res=True,
    )


def test_top_remove_increments_remove_count(collection):
    """Test that running a delete increments the remove count."""
    collection.insert_one({"_id": 1})
    collection.delete_one({"_id": 1})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data, {"remove.count": Gte(1)}, msg="remove.count should be >= 1", raw_res=True
    )


def test_top_remove_increments_writeLock_count(collection):
    """Test that running a delete increments the writeLock count."""
    collection.insert_one({"_id": 1})
    collection.delete_one({"_id": 1})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data,
        {"writeLock.count": Gte(1)},
        msg="writeLock.count should be >= 1 after delete",
        raw_res=True,
    )


def test_top_insert_time_positive_after_inserts(collection):
    """Test that insert.time is positive after inserting documents."""
    collection.insert_many([{"_id": i} for i in range(10)])
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data, {"insert.time": Gt(0)}, msg="insert.time should be > 0 after inserts", raw_res=True
    )


def test_top_query_time_positive_after_query(collection):
    """Test that queries.time is positive after running a find query."""
    collection.insert_one({"_id": 1})
    list(collection.find())
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data, {"queries.time": Gt(0)}, msg="queries.time should be > 0 after query", raw_res=True
    )


# ---------- Cross-Lock Consistency Invariants ----------


def _setup_mixed_operations(collection):
    """Insert, query, update, and delete on the collection to populate all counters."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    list(collection.find())
    collection.update_one({"_id": 0}, {"$set": {"a": 99}})
    collection.delete_one({"_id": 4})


def test_top_readLock_count_gte_queries_count(collection):
    """Test that readLock.count >= queries.count."""
    _setup_mixed_operations(collection)
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data,
        {"readLock.count": Gte(ns_data["queries"]["count"])},
        msg="readLock.count should be >= queries.count",
        raw_res=True,
    )


def test_top_readLock_time_gte_queries_time(collection):
    """Test that readLock.time >= queries.time."""
    _setup_mixed_operations(collection)
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data,
        {"readLock.time": Gte(ns_data["queries"]["time"])},
        msg="readLock.time should be >= queries.time",
        raw_res=True,
    )


def test_top_writeLock_count_gte_insert_update_remove(collection):
    """Test that writeLock.count >= insert.count + update.count + remove.count."""
    _setup_mixed_operations(collection)
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    write_sum = ns_data["insert"]["count"] + ns_data["update"]["count"] + ns_data["remove"]["count"]
    assertProperties(
        ns_data,
        {"writeLock.count": Gte(write_sum)},
        msg="writeLock.count should be >= insert+update+remove count",
        raw_res=True,
    )


def test_top_writeLock_time_gte_insert_update_remove(collection):
    """Test that writeLock.time >= insert.time + update.time + remove.time."""
    _setup_mixed_operations(collection)
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    write_sum = ns_data["insert"]["time"] + ns_data["update"]["time"] + ns_data["remove"]["time"]
    assertProperties(
        ns_data,
        {"writeLock.time": Gte(write_sum)},
        msg="writeLock.time should be >= insert+update+remove time",
        raw_res=True,
    )
