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


# Property [Global Field Boolean Acceptance]: setUserWriteBlockMode accepts only boolean values
# for the global field.
@pytest.mark.parametrize(
    "value",
    [pytest.param(True, id="global_true"), pytest.param(False, id="global_false")],
)
def test_setUserWriteBlockMode_global_valid(collection, value):
    """Test setUserWriteBlockMode accepts boolean global field."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": value})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setUserWriteBlockMode should accept boolean global field"
    )


# Property [Global Field Type Rejection]: setUserWriteBlockMode rejects all non-boolean types
# for the global field with no coercion.
@pytest.mark.parametrize(
    "value,error_code",
    [
        pytest.param(1, TYPE_MISMATCH_ERROR, id="int32_1"),
        pytest.param(0, TYPE_MISMATCH_ERROR, id="int32_0"),
        pytest.param(1.0, TYPE_MISMATCH_ERROR, id="double_1"),
        pytest.param(0.0, TYPE_MISMATCH_ERROR, id="double_0"),
        pytest.param(Int64(1), TYPE_MISMATCH_ERROR, id="int64"),
        pytest.param(Decimal128("1"), TYPE_MISMATCH_ERROR, id="decimal128"),
        pytest.param(FLOAT_NAN, TYPE_MISMATCH_ERROR, id="nan"),
        pytest.param(FLOAT_INFINITY, TYPE_MISMATCH_ERROR, id="infinity"),
        pytest.param(float("-inf"), TYPE_MISMATCH_ERROR, id="negative_infinity"),
        pytest.param(-0.0, TYPE_MISMATCH_ERROR, id="negative_zero"),
        pytest.param("true", TYPE_MISMATCH_ERROR, id="string"),
        pytest.param([], TYPE_MISMATCH_ERROR, id="array"),
        pytest.param({}, TYPE_MISMATCH_ERROR, id="object"),
        pytest.param(None, MISSING_FIELD_ERROR, id="null"),
    ],
)
def test_setUserWriteBlockMode_global_type_rejected(collection, value, error_code):
    """Test setUserWriteBlockMode rejects non-boolean global field."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": value})
    assertFailureCode(
        result, error_code, msg="setUserWriteBlockMode should reject non-boolean global field"
    )


# Property [Missing Global Field]: setUserWriteBlockMode requires the global field.
def test_setUserWriteBlockMode_missing_global_fails(collection):
    """Test setUserWriteBlockMode without global field fails."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1})
    assertFailureCode(
        result,
        MISSING_FIELD_ERROR,
        msg="setUserWriteBlockMode should require the global field",
    )


# Property [Reason Field Valid Values]: setUserWriteBlockMode accepts valid reason enum strings.
@pytest.mark.parametrize(
    "reason",
    [
        pytest.param("Unspecified", id="unspecified"),
        pytest.param("ClusterToClusterMigrationInProgress", id="cluster_migration"),
        pytest.param("DiskUseThresholdExceeded", id="disk_threshold"),
    ],
)
def test_setUserWriteBlockMode_reason_valid(collection, reason):
    """Test setUserWriteBlockMode accepts valid reason values."""
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": reason},
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setUserWriteBlockMode should accept valid reason string"
    )


# Property [Reason Field Optional]: the reason field can be omitted or null.
def test_setUserWriteBlockMode_reason_omitted_succeeds(collection):
    """Test setUserWriteBlockMode succeeds when reason field is omitted."""
    result = execute_admin_command(collection, {"setUserWriteBlockMode": 1, "global": True})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setUserWriteBlockMode should succeed without reason field"
    )


def test_setUserWriteBlockMode_reason_null_succeeds(collection):
    """Test setUserWriteBlockMode succeeds when reason is null."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": True, "reason": None}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setUserWriteBlockMode should treat null reason as omitted",
    )


# Property [Reason Field Type Rejection]: setUserWriteBlockMode rejects non-string types for
# the reason field.
@pytest.mark.parametrize(
    "value,error_code",
    [
        pytest.param(1, TYPE_MISMATCH_ERROR, id="int"),
        pytest.param(True, TYPE_MISMATCH_ERROR, id="bool"),
        pytest.param([], TYPE_MISMATCH_ERROR, id="array"),
        pytest.param({}, TYPE_MISMATCH_ERROR, id="object"),
    ],
)
def test_setUserWriteBlockMode_reason_type_rejected(collection, value, error_code):
    """Test setUserWriteBlockMode rejects non-string reason field."""
    result = execute_admin_command(
        collection, {"setUserWriteBlockMode": 1, "global": True, "reason": value}
    )
    assertFailureCode(
        result,
        error_code,
        msg="setUserWriteBlockMode should reject non-string reason field",
    )


# Property [Reason Field Invalid Enum]: setUserWriteBlockMode rejects unrecognized reason
# strings.
def test_setUserWriteBlockMode_reason_invalid_enum_fails(collection):
    """Test setUserWriteBlockMode rejects unrecognized reason string."""
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "InvalidReason"},
    )
    assertFailureCode(
        result,
        BAD_VALUE_ERROR,
        msg="setUserWriteBlockMode should reject unrecognized reason enum value",
    )


# Property [Unrecognized Fields]: setUserWriteBlockMode rejects unknown fields.
def test_setUserWriteBlockMode_unrecognized_field_fails(collection):
    """Test setUserWriteBlockMode rejects extra unrecognized fields."""
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": False, "unknownField": 1},
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setUserWriteBlockMode should reject unrecognized fields",
    )
