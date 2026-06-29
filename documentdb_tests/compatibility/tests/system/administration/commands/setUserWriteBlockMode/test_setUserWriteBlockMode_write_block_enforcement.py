"""Tests for setUserWriteBlockMode write block enforcement errors.

Validates that write operations are rejected while the block is active.
"""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.administration.commands.setUserWriteBlockMode.utils.write_block_helpers import (  # noqa: E501
    force_disable_write_block,
)
from documentdb_tests.compatibility.tests.system.administration.commands.utils.admin_test_case import (  # noqa: E501
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import USER_WRITES_BLOCKED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


@pytest.fixture(autouse=True)
def _manage_write_block(collection):
    """Ensure write block is disabled before and after each test."""
    force_disable_write_block(collection)
    yield
    force_disable_write_block(collection)


# Property [Write Operations Blocked]: all write operations are rejected while the block is
# active.
WRITE_BLOCKED_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "blocked_insert",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        indexes=[IndexModel([("a", 1)], name="a_1")],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": "blocked"}]},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block insert while active",
    ),
    AdminTestCase(
        "blocked_update",
        use_admin=False,
        docs=[{"_id": "seed", "a": 1}],
        indexes=[IndexModel([("a", 1)], name="a_1")],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
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
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
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
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
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
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
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
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
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
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"dropIndexes": ctx.collection, "index": "a_1"},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block dropIndexes while active",
    ),
    AdminTestCase(
        "blocked_drop_collection",
        use_admin=False,
        docs=[{"_id": "seed"}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"drop": ctx.collection},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block drop collection while active",
    ),
    AdminTestCase(
        "blocked_create_collection",
        use_admin=False,
        docs=[{"_id": "seed"}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"create": f"{ctx.collection}_blocked_new"},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block create collection while active",
    ),
    AdminTestCase(
        "blocked_dropDatabase",
        use_admin=False,
        docs=[{"_id": "seed"}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"dropDatabase": 1},
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block dropDatabase while active",
    ),
    AdminTestCase(
        "blocked_batch_insert",
        use_admin=False,
        docs=[{"_id": "seed"}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": "bulk1"}, {"_id": "bulk2"}],
        },
        error_code=USER_WRITES_BLOCKED_ERROR,
        msg="setUserWriteBlockMode should block multi-document insert while active",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_BLOCKED_TESTS))
def test_setUserWriteBlockMode_blocked(database_client, collection, test):
    """Test setUserWriteBlockMode blocks write operations while active."""
    collection = test.prepare(database_client, collection)
    test.run_pre_command(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertFailureCode(result, test.error_code, msg=test.msg)
