"""Tests for setUserWriteBlockMode core behavior.

Validates enable/disable semantics, idempotent behavior, and state restoration.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
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


# Property [Idempotent Disable]: disabling write block when no block is active succeeds.
def test_setUserWriteBlockMode_disable_when_no_block_active(collection):
    """Test setUserWriteBlockMode global:false when no block is active succeeds."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setUserWriteBlockMode should succeed when disabling with no active block",
    )


# Property [Write Restoration]: writes succeed after disabling a previously active block.
def test_setUserWriteBlockMode_enable_disable_restores_writes(collection):
    """Test setUserWriteBlockMode enable then disable allows writes again."""
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": "restore_test"}]}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setUserWriteBlockMode should allow writes after block is disabled",
    )


# Property [Repeated Toggle]: toggling write block multiple times does not produce errors.
def test_setUserWriteBlockMode_toggle_multiple_times(collection):
    """Test setUserWriteBlockMode toggling on and off multiple times succeeds."""
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setUserWriteBlockMode should succeed after repeated toggling",
    )


# Property [Idempotent Enable]: re-enabling with same default reason is idempotent.
def test_setUserWriteBlockMode_enable_idempotent_same_reason(collection):
    """Test setUserWriteBlockMode re-enable with same reason is idempotent."""
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setUserWriteBlockMode should be idempotent when re-enabling with same reason",
    )
