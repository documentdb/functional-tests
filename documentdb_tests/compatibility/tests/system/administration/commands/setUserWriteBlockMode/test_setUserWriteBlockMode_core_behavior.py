"""Tests for setUserWriteBlockMode core behavior.

Validates enable/disable semantics, response structure, idempotent behavior,
and state restoration.
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


def test_setUserWriteBlockMode_enable_returns_ok(collection):
    """Test setUserWriteBlockMode with global:true returns ok:1."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should return ok:1 on enable")


def test_setUserWriteBlockMode_disable_returns_ok(collection):
    """Test setUserWriteBlockMode with global:false returns ok:1."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should return ok:1 on disable")


def test_setUserWriteBlockMode_disable_when_no_block_active_idempotent(collection):
    """Test global:false when no block is active succeeds (idempotent)."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="Should succeed when disabling with no active block"
    )


def test_setUserWriteBlockMode_enable_disable_cycle_restores_writes(collection):
    """Test enable block then disable, verify writes succeed again."""
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": "restore_test"}]}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Write should succeed after block disabled")


def test_setUserWriteBlockMode_toggle_multiple_times_no_error(collection):
    """Test toggling write block off and on multiple times without errors."""
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed after repeated toggling")


def test_setUserWriteBlockMode_enable_idempotent_same_reason(collection):
    """Test enabling write block again with same default reason is idempotent."""
    execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="Should succeed when re-enabling with same reason"
    )


def test_setUserWriteBlockMode_response_contains_ok_field(collection):
    """Test successful command returns document with ok:1."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Response should contain ok:1")
