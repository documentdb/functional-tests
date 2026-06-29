"""Tests for setUserWriteBlockMode write block enforcement.

Validates that write operations are blocked while the block is active,
read operations are not affected, and operations succeed when block is disabled.
"""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.administration.commands.utils.admin_test_case import (  # noqa: E501
    AdminTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import USER_WRITES_BLOCKED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

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
WRITE_BLOCKED_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "blocked_insert",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        indexes=[IndexModel([("a", 1)], name="a_1")],
        pre_command=_enable_write_block,
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": "blocked"}]},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block insert while active",
    ),
    AdminTestCase(
        "blocked_update",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        indexes=[IndexModel([("a", 1)], name="a_1")],
        pre_command=_enable_write_block,
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {}, "u": {"$set": {"x": 2}}}],
        },
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block update while active",
    ),
    AdminTestCase(
        "blocked_delete",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        indexes=[IndexModel([("a", 1)], name="a_1")],
        pre_command=_enable_write_block,
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 1}],
        },
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block delete while active",
    ),
    AdminTestCase(
        "blocked_findAndModify_update",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        pre_command=_enable_write_block,
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {},
            "update": {"$set": {"x": 2}},
        },
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block findAndModify update while active",
    ),
    AdminTestCase(
        "blocked_findAndModify_remove",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        pre_command=_enable_write_block,
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {},
            "remove": True,
        },
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block findAndModify remove while active",
    ),
    AdminTestCase(
        "blocked_createIndexes",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        pre_command=_enable_write_block,
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [{"key": {"blocked_field": 1}, "name": "blocked_field_1"}],
        },
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block createIndexes while active",
    ),
    AdminTestCase(
        "blocked_dropIndexes",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        indexes=[IndexModel([("a", 1)], name="a_1")],
        pre_command=_enable_write_block,
        command=lambda ctx: {"dropIndexes": ctx.collection, "index": "a_1"},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block dropIndexes while active",
    ),
    AdminTestCase(
        "blocked_drop_collection",
        use_admin=False,
        docs=[{"_id": "seed"}],
        pre_command=_enable_write_block,
        command=lambda ctx: {"drop": ctx.collection},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block drop collection while active",
    ),
    AdminTestCase(
        "blocked_create_collection",
        use_admin=False,
        docs=[{"_id": "seed"}],
        pre_command=_enable_write_block,
        command=lambda ctx: {"create": f"{ctx.collection}_blocked_new"},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block create collection while active",
    ),
    AdminTestCase(
        "blocked_dropDatabase",
        use_admin=False,
        docs=[{"_id": "seed"}],
        pre_command=_enable_write_block,
        command=lambda ctx: {"dropDatabase": 1},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block dropDatabase while active",
    ),
]

# Property [Read Operations Not Blocked]: read operations succeed while the block is active.
READ_NOT_BLOCKED_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "read_find",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "read_doc", "x": 1}],
        pre_command=_enable_write_block,
        command=lambda ctx: {"find": ctx.collection, "filter": {}},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should not block find while active",
    ),
    AdminTestCase(
        "read_aggregate",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "read_doc", "x": 1}],
        pre_command=_enable_write_block,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {}}],
            "cursor": {},
        },
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should not block aggregate while active",
    ),
    AdminTestCase(
        "read_count",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "read_doc", "x": 1}],
        pre_command=_enable_write_block,
        command=lambda ctx: {"count": ctx.collection},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should not block count while active",
    ),
    AdminTestCase(
        "read_distinct",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "read_doc", "x": 1}],
        pre_command=_enable_write_block,
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should not block distinct while active",
    ),
]

# Property [Writes Succeed When Disabled]: write operations succeed when no block is active.
WRITE_SUCCEEDS_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "succeeds_insert",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "upd", "x": 1}, {"_id": "del"}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": "ok"}]},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should allow insert when block is not active",
    ),
    AdminTestCase(
        "succeeds_update",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "upd", "x": 1}, {"_id": "del"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": "upd"}, "u": {"$set": {"x": 2}}}],
        },
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should allow update when block is not active",
    ),
    AdminTestCase(
        "succeeds_delete",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "upd", "x": 1}, {"_id": "del"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": "del"}, "limit": 1}],
        },
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should allow delete when block is not active",
    ),
]

ENFORCEMENT_TESTS: list[AdminTestCase] = (
    WRITE_BLOCKED_TESTS + READ_NOT_BLOCKED_TESTS + WRITE_SUCCEEDS_TESTS
)

ENFORCEMENT_ERROR_TESTS: list[AdminTestCase] = WRITE_BLOCKED_TESTS
ENFORCEMENT_SUCCESS_TESTS: list[AdminTestCase] = READ_NOT_BLOCKED_TESTS + WRITE_SUCCEEDS_TESTS


@pytest.mark.parametrize("test", pytest_params(ENFORCEMENT_ERROR_TESTS))
def test_setUserWriteBlockMode_blocked(database_client, collection, test):
    """Test setUserWriteBlockMode blocks write operations while active."""
    collection = test.prepare(database_client, collection)
    test.run_pre_command(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(ENFORCEMENT_SUCCESS_TESTS))
def test_setUserWriteBlockMode_allowed(database_client, collection, test):
    """Test setUserWriteBlockMode allows reads and writes when appropriate."""
    collection = test.prepare(database_client, collection)
    test.run_pre_command(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.expected, msg=test.msg)
