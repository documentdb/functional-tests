"""Tests for killOp command core behavior.

Validates killOp response structure, behavior with non-existent operations,
and edge cases for opId values.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    NON_RUNNING_OP_ID,
)

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_killOp_nonexistent_opid_returns_ok(collection):
    """Test killOp with opId that does not correspond to any running operation returns ok:1."""
    result = execute_admin_command(collection, {"killOp": 1, "op": NON_RUNNING_OP_ID})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "info": "attempting to kill op"},
        msg="Should return ok:1 for non-existent opId",
    )


def test_killOp_op_int32_min(collection):
    """Test killOp with minimum int32 opId returns ok:1."""
    result = execute_admin_command(collection, {"killOp": 1, "op": INT32_MIN})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "info": "attempting to kill op"},
        msg="Should return ok:1 for INT32_MIN opId",
    )


def test_killOp_op_zero(collection):
    """Test killOp with zero opId returns ok:1."""
    result = execute_admin_command(collection, {"killOp": 1, "op": INT32_ZERO})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "info": "attempting to kill op"},
        msg="Should return ok:1 for opId 0",
    )


def test_killOp_op_int32_max(collection):
    """Test killOp with maximum int32 opId returns ok:1."""
    result = execute_admin_command(collection, {"killOp": 1, "op": INT32_MAX})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "info": "attempting to kill op"},
        msg="Should return ok:1 for INT32_MAX opId",
    )


def test_killOp_op_int32_max_as_double(collection):
    """Test killOp accepts INT32_MAX as a whole-number double."""
    result = execute_admin_command(collection, {"killOp": 1, "op": float(INT32_MAX)})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "info": "attempting to kill op"},
        msg="Should return ok:1 for INT32_MAX as a double",
    )


def test_killOp_op_int32_min_as_double(collection):
    """Test killOp accepts INT32_MIN as a whole-number double."""
    result = execute_admin_command(collection, {"killOp": 1, "op": float(INT32_MIN)})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "info": "attempting to kill op"},
        msg="Should return ok:1 for INT32_MIN as a double",
    )


def test_killOp_extra_unrecognized_field(collection):
    """Test killOp with unrecognized top-level field is accepted (not rejected)."""
    result = execute_admin_command(
        collection, {"killOp": 1, "op": NON_RUNNING_OP_ID, "unknownField": 1}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "info": "attempting to kill op"},
        msg="Should ignore unrecognized fields",
    )
