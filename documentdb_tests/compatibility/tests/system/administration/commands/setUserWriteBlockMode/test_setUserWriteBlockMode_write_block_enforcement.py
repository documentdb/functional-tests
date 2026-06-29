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


# Property [Write Operations Blocked]: all write operations are rejected while the block is
# active.
_WRITE_BLOCKED_PARAMS = [
    pytest.param(
        lambda name: {"insert": name, "documents": [{"_id": "blocked"}]},
        id="insert",
    ),
    pytest.param(
        lambda name: {"update": name, "updates": [{"q": {}, "u": {"$set": {"x": 2}}}]},
        id="update",
    ),
    pytest.param(
        lambda name: {"delete": name, "deletes": [{"q": {}, "limit": 1}]},
        id="delete",
    ),
    pytest.param(
        lambda name: {"findAndModify": name, "query": {}, "update": {"$set": {"x": 2}}},
        id="findAndModify_update",
    ),
    pytest.param(
        lambda name: {"findAndModify": name, "query": {}, "remove": True},
        id="findAndModify_remove",
    ),
    pytest.param(
        lambda name: {
            "createIndexes": name,
            "indexes": [{"key": {"blocked_field": 1}, "name": "blocked_field_1"}],
        },
        id="createIndexes",
    ),
    pytest.param(
        lambda name: {"dropIndexes": name, "index": "a_1"},
        id="dropIndexes",
    ),
    pytest.param(
        lambda name: {"drop": name},
        id="drop_collection",
    ),
    pytest.param(
        lambda name: {"create": f"{name}_blocked_new"},
        id="create_collection",
    ),
    pytest.param(
        lambda name: {"dropDatabase": 1},
        id="dropDatabase",
    ),
]


@pytest.mark.parametrize("build_command", _WRITE_BLOCKED_PARAMS)
def test_setUserWriteBlockMode_write_operation_blocked(collection, build_command):
    """Test write operation is rejected while write block is active."""
    collection.insert_one({"_id": "seed", "a": 1})
    collection.create_index([("a", 1)], name="a_1")
    _enable_write_block(collection)
    command = build_command(collection.name)
    result = execute_command(collection, command)
    assertFailureCode(
        result,
        USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block write operations while active",
    )


# Property [Read Operations Not Blocked]: read operations succeed while the block is active.
_READ_NOT_BLOCKED_PARAMS = [
    pytest.param(
        lambda name: {"find": name, "filter": {}},
        id="find",
    ),
    pytest.param(
        lambda name: {"aggregate": name, "pipeline": [{"$match": {}}], "cursor": {}},
        id="aggregate",
    ),
    pytest.param(
        lambda name: {"count": name},
        id="count",
    ),
    pytest.param(
        lambda name: {"distinct": name, "key": "x"},
        id="distinct",
    ),
]


@pytest.mark.parametrize("build_command", _READ_NOT_BLOCKED_PARAMS)
def test_setUserWriteBlockMode_read_operation_not_blocked(collection, build_command):
    """Test read operation succeeds while write block is active."""
    collection.insert_one({"_id": "read_doc", "x": 1})
    _enable_write_block(collection)
    command = build_command(collection.name)
    result = execute_command(collection, command)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setUserWriteBlockMode should not block read operations",
    )


# Property [Writes Succeed When Disabled]: write operations succeed when no block is active.
_WRITE_SUCCEEDS_PARAMS = [
    pytest.param(
        lambda name: {"insert": name, "documents": [{"_id": "ok"}]},
        id="insert",
    ),
    pytest.param(
        lambda name: {"update": name, "updates": [{"q": {"_id": "upd"}, "u": {"$set": {"x": 2}}}]},
        id="update",
    ),
    pytest.param(
        lambda name: {"delete": name, "deletes": [{"q": {"_id": "del"}, "limit": 1}]},
        id="delete",
    ),
]


@pytest.mark.parametrize("build_command", _WRITE_SUCCEEDS_PARAMS)
def test_setUserWriteBlockMode_write_succeeds_when_disabled(collection, build_command):
    """Test write operation succeeds when write block is not active."""
    collection.insert_one({"_id": "upd", "x": 1})
    collection.insert_one({"_id": "del"})
    command = build_command(collection.name)
    result = execute_command(collection, command)
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setUserWriteBlockMode should allow writes when block is not active",
    )
