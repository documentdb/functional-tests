"""Tests for setUserWriteBlockMode write block enforcement.

Validates that write operations are blocked while the block is active,
read operations are not affected, and operations succeed when block is disabled.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import USER_WRITES_BLOCKED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


def _force_disable_write_block(collection):
    """Force-disable write block regardless of current reason."""
    admin = collection.database.client.admin
    try:
        admin.command({"setUserWriteBlockMode": 1, "global": False})
        return
    except Exception:
        pass
    for reason in [
        "Unspecified",
        "ClusterToClusterMigrationInProgress",
        "DiskUseThresholdExceeded",
    ]:
        try:
            admin.command({"setUserWriteBlockMode": 1, "global": False, "reason": reason})
            return
        except Exception:
            continue


@pytest.fixture(autouse=True)
def _manage_write_block(collection):
    """Ensure write block is disabled before and after each test."""
    _force_disable_write_block(collection)
    yield
    _force_disable_write_block(collection)


def _enable_write_block(collection):
    """Enable write block."""
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})


# --- Writes blocked while block is active ---


def test_setUserWriteBlockMode_insert_blocked(collection):
    """Test insert is rejected with UserWritesBlocked while write block is active."""
    _enable_write_block(collection)
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": "blocked"}]}
    )
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="Insert should be blocked")


def test_setUserWriteBlockMode_update_blocked(collection):
    """Test update is rejected with UserWritesBlocked while write block is active."""
    collection.insert_one({"_id": "upd_target", "x": 1})
    _enable_write_block(collection)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": "upd_target"}, "u": {"$set": {"x": 2}}}],
        },
    )
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="Update should be blocked")


def test_setUserWriteBlockMode_delete_blocked(collection):
    """Test delete is rejected with UserWritesBlocked while write block is active."""
    collection.insert_one({"_id": "del_target"})
    _enable_write_block(collection)
    result = execute_command(
        collection,
        {"delete": collection.name, "deletes": [{"q": {"_id": "del_target"}, "limit": 1}]},
    )
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="Delete should be blocked")


def test_setUserWriteBlockMode_findAndModify_update_blocked(collection):
    """Test findAndModify with update is blocked while write block is active."""
    collection.insert_one({"_id": "fam_target", "x": 1})
    _enable_write_block(collection)
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": "fam_target"},
            "update": {"$set": {"x": 2}},
        },
    )
    assertFailureCode(
        result, USER_WRITES_BLOCKED_ERROR, msg="findAndModify update should be blocked"
    )


def test_setUserWriteBlockMode_findAndModify_delete_blocked(collection):
    """Test findAndModify with remove is blocked while write block is active."""
    collection.insert_one({"_id": "fam_del"})
    _enable_write_block(collection)
    result = execute_command(
        collection,
        {"findAndModify": collection.name, "query": {"_id": "fam_del"}, "remove": True},
    )
    assertFailureCode(
        result, USER_WRITES_BLOCKED_ERROR, msg="findAndModify remove should be blocked"
    )


def test_setUserWriteBlockMode_createIndexes_blocked(collection):
    """Test createIndexes is blocked while write block is active."""
    collection.insert_one({"_id": "idx_doc", "a": 1})
    _enable_write_block(collection)
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}],
        },
    )
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="createIndexes should be blocked")


def test_setUserWriteBlockMode_dropIndexes_blocked(collection):
    """Test dropIndexes is blocked while write block is active."""
    collection.insert_one({"_id": "didx", "a": 1})
    collection.create_index([("a", 1)], name="a_1_to_drop")
    _enable_write_block(collection)
    result = execute_command(collection, {"dropIndexes": collection.name, "index": "a_1_to_drop"})
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="dropIndexes should be blocked")


def test_setUserWriteBlockMode_drop_collection_blocked(collection):
    """Test drop collection is blocked while write block is active."""
    collection.insert_one({"_id": "drop_coll"})
    _enable_write_block(collection)
    result = execute_command(collection, {"drop": collection.name})
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="Drop collection should be blocked")


def test_setUserWriteBlockMode_create_collection_blocked(collection):
    """Test creating a collection is blocked while write block is active."""
    _enable_write_block(collection)
    result = execute_command(collection, {"create": "blocked_new_coll"})
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="Create collection should be blocked")


def test_setUserWriteBlockMode_dropDatabase_blocked(database_client):
    """Test dropDatabase is blocked while write block is active."""
    coll = database_client.create_collection("db_to_drop")
    coll.insert_one({"_id": "seed"})
    execute_admin_command(coll, {"setUserWriteBlockMode": 1, "global": True})
    result = execute_command(coll, {"dropDatabase": 1})
    assertFailureCode(result, USER_WRITES_BLOCKED_ERROR, msg="dropDatabase should be blocked")
    execute_admin_command(coll, {"setUserWriteBlockMode": 1, "global": False})


# --- Reads not blocked while block is active ---


def test_setUserWriteBlockMode_find_not_blocked(collection):
    """Test find succeeds while write block is active."""
    collection.insert_one({"_id": "read_doc", "val": 42})
    _enable_write_block(collection)
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": "read_doc"}})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Find should succeed while block active")


def test_setUserWriteBlockMode_aggregate_read_not_blocked(collection):
    """Test aggregate with no write stages succeeds while write block is active."""
    collection.insert_one({"_id": "agg_doc", "val": 1})
    _enable_write_block(collection)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$match": {"val": 1}}], "cursor": {}},
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="Aggregate read should succeed while block active"
    )


def test_setUserWriteBlockMode_count_not_blocked(collection):
    """Test count succeeds while write block is active."""
    collection.insert_one({"_id": "count_doc"})
    _enable_write_block(collection)
    result = execute_command(collection, {"count": collection.name})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Count should succeed while block active")


def test_setUserWriteBlockMode_distinct_not_blocked(collection):
    """Test distinct succeeds while write block is active."""
    collection.insert_one({"_id": "dist_doc", "x": 1})
    _enable_write_block(collection)
    result = execute_command(collection, {"distinct": collection.name, "key": "x"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Distinct should succeed while block active")


# --- Writes succeed when block is disabled ---


def test_setUserWriteBlockMode_insert_succeeds_when_disabled(collection):
    """Test insert succeeds when write block is not active."""
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": "not_blocked"}]}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Insert should succeed with no block")


def test_setUserWriteBlockMode_update_succeeds_when_disabled(collection):
    """Test update succeeds when write block is not active."""
    collection.insert_one({"_id": "upd_ok", "x": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": "upd_ok"}, "u": {"$set": {"x": 2}}}]},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Update should succeed with no block")


def test_setUserWriteBlockMode_delete_succeeds_when_disabled(collection):
    """Test delete succeeds when write block is not active."""
    collection.insert_one({"_id": "del_ok"})
    result = execute_command(
        collection,
        {"delete": collection.name, "deletes": [{"q": {"_id": "del_ok"}, "limit": 1}]},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Delete should succeed with no block")
