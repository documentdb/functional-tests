"""Tests for setUserWriteBlockMode success cases.

Validates argument acceptance, read operations not blocked while active,
and write operations succeeding when block is disabled.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.administration.commands.setUserWriteBlockMode.utils.write_block_helpers import (  # noqa: E501
    force_disable_write_block,
)
from documentdb_tests.compatibility.tests.system.administration.commands.utils.admin_test_case import (  # noqa: E501
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


@pytest.fixture(autouse=True)
def _manage_write_block(collection):
    """Ensure write block is disabled before and after each test."""
    force_disable_write_block(collection)
    yield
    force_disable_write_block(collection)


# Property [Global Field Boolean Acceptance]: setUserWriteBlockMode accepts only boolean values
# for the global field.
GLOBAL_VALID_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "global_true",
        command=lambda ctx: {"setUserWriteBlockMode": 1, "global": True},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should accept global:true",
    ),
    AdminTestCase(
        "global_false",
        command=lambda ctx: {"setUserWriteBlockMode": 1, "global": False},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should accept global:false",
    ),
]

# Property [Reason Field Valid Values]: setUserWriteBlockMode accepts valid reason enum strings.
REASON_VALID_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        f"reason_{tid}",
        command=lambda ctx, r=reason: {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": r,
        },
        expected={"ok": 1.0},
        msg=f"setUserWriteBlockMode should accept reason:{reason}",
    )
    for tid, reason in [
        ("unspecified", "Unspecified"),
        ("cluster_migration", "ClusterToClusterMigrationInProgress"),
        ("disk_threshold", "DiskUseThresholdExceeded"),
    ]
]

# Property [Reason Field Optional]: the reason field can be null (treated as omitted).
REASON_OPTIONAL_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "reason_null",
        command=lambda ctx: {"setUserWriteBlockMode": 1, "global": True, "reason": None},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should treat null reason as omitted",
    ),
]

# Property [Read Operations Not Blocked]: read operations succeed while the block is active.
READ_NOT_BLOCKED_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "read_find",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "read_doc", "x": 1}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"find": ctx.collection, "filter": {}},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should not block find while active",
    ),
    AdminTestCase(
        "read_aggregate",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "read_doc", "x": 1}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
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
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"count": ctx.collection},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should not block count while active",
    ),
    AdminTestCase(
        "read_distinct",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "read_doc", "x": 1}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
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

ACCEPTANCE_TESTS: list[AdminTestCase] = (
    GLOBAL_VALID_TESTS + REASON_VALID_TESTS + REASON_OPTIONAL_TESTS
)

ADMIN_SUCCESS_TESTS: list[AdminTestCase] = ACCEPTANCE_TESTS
COLLECTION_SUCCESS_TESTS: list[AdminTestCase] = READ_NOT_BLOCKED_TESTS + WRITE_SUCCEEDS_TESTS


@pytest.mark.parametrize("test", pytest_params(ADMIN_SUCCESS_TESTS))
def test_setUserWriteBlockMode_acceptance(collection, test):
    """Test setUserWriteBlockMode accepts valid arguments."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(COLLECTION_SUCCESS_TESTS))
def test_setUserWriteBlockMode_allowed(database_client, collection, test):
    """Test setUserWriteBlockMode allows reads and writes when appropriate."""
    collection = test.prepare(database_client, collection)
    test.run_pre_command(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.expected, msg=test.msg)
