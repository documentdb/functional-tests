"""Tests for setUserWriteBlockMode argument validation.

Validates type checking for the global and reason fields, unrecognized fields,
and command value handling.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, FLOAT_NAN

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


# --- global field: valid boolean values ---


def test_setUserWriteBlockMode_global_true_succeeds(collection):
    """Test global:true (boolean) succeeds."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="global:true should succeed")


def test_setUserWriteBlockMode_global_false_succeeds(collection):
    """Test global:false (boolean) succeeds."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    assertSuccessPartial(result, {"ok": 1.0}, msg="global:false should succeed")


# --- global field: numeric types rejected (no coercion) ---


def test_setUserWriteBlockMode_global_int_1_rejected(collection):
    """Test global:1 (int32) is rejected — no coercion to bool."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": 1})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:int should be rejected")


def test_setUserWriteBlockMode_global_int_0_rejected(collection):
    """Test global:0 (int32) is rejected — no coercion to bool."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": 0})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:int(0) should be rejected")


def test_setUserWriteBlockMode_global_double_1_rejected(collection):
    """Test global:1.0 (double) is rejected — no coercion to bool."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": 1.0})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:double should be rejected")


def test_setUserWriteBlockMode_global_double_0_rejected(collection):
    """Test global:0.0 (double) is rejected — no coercion to bool."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": 0.0})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:double(0.0) should be rejected")


def test_setUserWriteBlockMode_global_int64_rejected(collection):
    """Test global:NumberLong(1) (int64) is rejected — no coercion to bool."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": Int64(1)})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:int64 should be rejected")


def test_setUserWriteBlockMode_global_decimal128_rejected(collection):
    """Test global:NumberDecimal('1') (decimal128) is rejected — no coercion to bool."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": Decimal128("1")}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:decimal128 should be rejected")


def test_setUserWriteBlockMode_global_nan_rejected(collection):
    """Test global:NaN (double) is rejected — no coercion to bool."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": FLOAT_NAN})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:NaN should be rejected")


def test_setUserWriteBlockMode_global_infinity_rejected(collection):
    """Test global:Infinity (double) is rejected — no coercion to bool."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": FLOAT_INFINITY}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:Infinity should be rejected")


def test_setUserWriteBlockMode_global_negative_infinity_rejected(collection):
    """Test global:-Infinity (double) is rejected — no coercion to bool."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": float("-inf")}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:-Infinity should be rejected")


def test_setUserWriteBlockMode_global_negative_zero_rejected(collection):
    """Test global:-0.0 (negative zero double) is rejected — no coercion to bool."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": -0.0})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:-0.0 should be rejected")


# --- global field: non-numeric invalid types ---


def test_setUserWriteBlockMode_global_null_fails(collection):
    """Test global:null is treated as missing required field."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": None})
    assertFailureCode(result, MISSING_FIELD_ERROR, msg="global:null should fail as missing")


def test_setUserWriteBlockMode_global_string_fails(collection):
    """Test global:'true' (string) fails with type error."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": "true"})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:string should fail")


def test_setUserWriteBlockMode_global_array_fails(collection):
    """Test global:[] (array) fails with type error."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": []})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:array should fail")


def test_setUserWriteBlockMode_global_object_fails(collection):
    """Test global:{} (object) fails with type error."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": {}})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="global:object should fail")


# --- missing global field ---


def test_setUserWriteBlockMode_missing_global_fails(collection):
    """Test setUserWriteBlockMode without global field fails with missing field error."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1})
    assertFailureCode(result, MISSING_FIELD_ERROR, msg="Missing global should fail")


# --- reason field: valid values ---


def test_setUserWriteBlockMode_reason_unspecified_succeeds(collection):
    """Test reason:'Unspecified' succeeds."""
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="reason:Unspecified should succeed")


def test_setUserWriteBlockMode_reason_cluster_migration_succeeds(collection):
    """Test reason:'ClusterToClusterMigrationInProgress' succeeds."""
    result = execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": "ClusterToClusterMigrationInProgress",
        },
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="reason:ClusterToClusterMigrationInProgress should succeed"
    )


def test_setUserWriteBlockMode_reason_disk_threshold_succeeds(collection):
    """Test reason:'DiskUseThresholdExceeded' succeeds."""
    result = execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": "DiskUseThresholdExceeded",
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="reason:DiskUseThresholdExceeded should succeed")


def test_setUserWriteBlockMode_no_reason_field_succeeds(collection):
    """Test omitting reason field succeeds (defaults to Unspecified)."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Omitting reason should succeed")


def test_setUserWriteBlockMode_reason_null_succeeds(collection):
    """Test reason:null is treated as omitted and succeeds."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": True, "reason": None}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="reason:null should succeed as omitted")


# --- reason field: invalid types ---


def test_setUserWriteBlockMode_reason_int_fails(collection):
    """Test reason:1 (int) fails with type error."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": True, "reason": 1}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="reason:int should fail")


def test_setUserWriteBlockMode_reason_bool_fails(collection):
    """Test reason:true (bool) fails with type error."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": True, "reason": True}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="reason:bool should fail")


def test_setUserWriteBlockMode_reason_array_fails(collection):
    """Test reason:[] (array) fails with type error."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": True, "reason": []}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="reason:array should fail")


def test_setUserWriteBlockMode_reason_object_fails(collection):
    """Test reason:{} (object) fails with type error."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": True, "reason": {}}
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="reason:object should fail")


def test_setUserWriteBlockMode_reason_invalid_enum_fails(collection):
    """Test reason with unrecognized string value fails with BadValue."""
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "InvalidReason"},
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Invalid reason enum should fail")


# --- unrecognized fields ---


def test_setUserWriteBlockMode_unrecognized_field_fails(collection):
    """Test setUserWriteBlockMode with extra unrecognized field fails."""
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": False, "unknownField": 1},
    )
    assertFailureCode(
        result, UNRECOGNIZED_COMMAND_FIELD_ERROR, msg="Unrecognized field should fail"
    )


# --- command field value ---


def test_setUserWriteBlockMode_command_value_1_succeeds(collection):
    """Test setUserWriteBlockMode:1 is the correct command value."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": False})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Command value 1 should succeed")
