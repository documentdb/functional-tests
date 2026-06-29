"""Tests for setUserWriteBlockMode error cases.

Validates mismatched reason errors when changing the reason on an active block.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.administration.commands.utils.admin_test_case import (  # noqa: E501
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import ILLEGAL_OPERATION_ERROR
from documentdb_tests.framework.executor import execute_admin_command
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


# Property [Mismatched Reason on Enable]: re-enabling with a different reason fails.
def test_setUserWriteBlockMode_enable_mismatched_reason_fails(collection):
    """Test setUserWriteBlockMode re-enable with different reason fails."""
    execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    result = execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": "ClusterToClusterMigrationInProgress",
        },
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="setUserWriteBlockMode should reject mismatched reason on re-enable",
    )


# Property [Mismatched Reason on Disable]: disabling with a different reason than the active
# block fails.
def test_setUserWriteBlockMode_disable_mismatched_reason_fails(collection):
    """Test setUserWriteBlockMode disable with different reason fails."""
    execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    result = execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": False,
            "reason": "ClusterToClusterMigrationInProgress",
        },
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="setUserWriteBlockMode should reject mismatched reason on disable",
    )


# Property [Same Reason Idempotent]: re-enabling with same explicit reason succeeds.
SAME_REASON_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        f"same_reason_{tid}",
        command=lambda ctx, r=reason: {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": r,
        },
        expected={"ok": 1.0},
        msg=f"setUserWriteBlockMode should be idempotent with same reason {reason}",
    )
    for tid, reason in [
        ("unspecified", "Unspecified"),
        ("cluster_migration", "ClusterToClusterMigrationInProgress"),
    ]
]


@pytest.mark.parametrize("test", pytest_params(SAME_REASON_TESTS))
def test_setUserWriteBlockMode_same_reason_idempotent(collection, test):
    """Test setUserWriteBlockMode re-enable with same reason is idempotent."""
    ctx = CommandContext.from_collection(collection)
    # First enable with the reason.
    execute_admin_command(collection, test.build_command(ctx))
    # Re-enable with same reason should succeed.
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
