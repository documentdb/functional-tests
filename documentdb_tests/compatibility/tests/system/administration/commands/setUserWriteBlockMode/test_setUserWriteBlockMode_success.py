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


# Global-field boolean acceptance (global:true/false) and valid reason enum acceptance are
# covered by test_setUserWriteBlockMode_core_behavior.py (enable/disable and idempotent-reason
# tests), so they are not duplicated here.

# Property [Reason Field Optional]: the reason field can be null. reason_null checks the command
# accepts null; reason_null_treated_as_omitted checks null behaves like an omitted reason, proven
# via a write (a no-reason disable only matches, restoring writes, if null was treated as omitted).
REASON_OPTIONAL_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "reason_null",
        command=lambda ctx: {"setUserWriteBlockMode": 1, "global": True, "reason": None},
        expected={"ok": 1.0},
        msg="setUserWriteBlockMode should accept null reason",
    ),
    AdminTestCase(
        "reason_null_treated_as_omitted",
        use_admin=False,
        partial_success=True,
        docs=[],
        pre_command=lambda c: (
            execute_admin_command(c, {"setUserWriteBlockMode": 1, "global": True, "reason": None}),
            execute_admin_command(c, {"setUserWriteBlockMode": 1, "global": False}),
        ),
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": "null_reason_write"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="setUserWriteBlockMode should treat null reason as omitted so writes resume",
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
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": "read_doc"}},
        expected={"ok": 1.0, "cursor": {"firstBatch": [{"_id": "read_doc", "x": 1}]}},
        msg="setUserWriteBlockMode should not block find while active",
    ),
    AdminTestCase(
        "read_aggregate",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "agg_doc", "x": 5}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"_id": "agg_doc"}}],
            "cursor": {},
        },
        expected={"ok": 1.0, "cursor": {"firstBatch": [{"_id": "agg_doc", "x": 5}]}},
        msg="setUserWriteBlockMode should not block aggregate while active",
    ),
    AdminTestCase(
        "read_count",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "c1"}, {"_id": "c2"}, {"_id": "c3"}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"count": ctx.collection},
        expected={"ok": 1.0, "n": 3},
        msg="setUserWriteBlockMode should not block count while active",
    ),
    AdminTestCase(
        "read_distinct",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "d1", "x": 1}, {"_id": "d2", "x": 2}, {"_id": "d3", "x": 1}],
        pre_command=lambda c: execute_admin_command(
            c, {"setUserWriteBlockMode": 1, "global": True}
        ),
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"ok": 1.0, "values": [1, 2]},
        msg="setUserWriteBlockMode should not block distinct while active",
    ),
]

# Property [Writes Succeed When Disabled]: write operations succeed when no block is active.
WRITE_SUCCEEDS_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "write_insert_no_block",
        use_admin=False,
        partial_success=True,
        docs=[],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": "new_doc", "v": 42}]},
        expected={"ok": 1.0, "n": 1},
        msg="setUserWriteBlockMode should allow insert when block is not active",
    ),
    AdminTestCase(
        "write_update_no_block",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "target", "x": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": "target"}, "u": {"$set": {"x": 99}}}],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="setUserWriteBlockMode should allow update when block is not active",
    ),
    AdminTestCase(
        "write_delete_no_block",
        use_admin=False,
        partial_success=True,
        docs=[{"_id": "target"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": "target"}, "limit": 1}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="setUserWriteBlockMode should allow delete when block is not active",
    ),
]

SUCCESS_TESTS: list[AdminTestCase] = (
    REASON_OPTIONAL_TESTS + READ_NOT_BLOCKED_TESTS + WRITE_SUCCEEDS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_setUserWriteBlockMode_success(database_client, collection, test):
    """Test setUserWriteBlockMode success cases."""
    collection = test.prepare(database_client, collection)
    test.run_pre_command(collection)
    ctx = CommandContext.from_collection(collection)
    if test.use_admin:
        result = execute_admin_command(collection, test.build_command(ctx))
    else:
        result = execute_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.expected, msg=test.msg)
