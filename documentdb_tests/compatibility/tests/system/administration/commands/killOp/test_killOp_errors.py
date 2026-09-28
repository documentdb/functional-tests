"""Tests for killOp command error cases.

Consolidates all failure-asserting test cases for the killOp command:
non-admin database rejection, missing op field, and invalid op values
(non-integral, or a valid integer outside the int32 range).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    KILLOP_OPID_NOT_INT32_ERROR,
    NO_SUCH_KEY_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.test_constants import (
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
    NON_RUNNING_OP_ID,
)

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_killOp_op_fractional_double_rejected(collection):
    """Test killOp rejects a fractional double op value."""
    result = execute_admin_command(collection, {"killOp": 1, "op": 3.14})
    assertFailureCode(result, BAD_VALUE_ERROR, msg="killOp should reject a non-integral op value")


def test_killOp_op_fractional_decimal_rejected(collection):
    """Test killOp rejects a fractional decimal op value."""
    result = execute_admin_command(collection, {"killOp": 1, "op": Decimal128("3.14")})
    assertFailureCode(result, BAD_VALUE_ERROR, msg="killOp should reject a non-integral op value")


def test_killOp_op_nearly_int_double_rejected(collection):
    """Test killOp rejects a double that is very close to but not an integer."""
    result = execute_admin_command(collection, {"killOp": 1, "op": 0.9999999999999999})
    assertFailureCode(result, BAD_VALUE_ERROR, msg="killOp should reject a non-integral op value")


def test_killOp_op_double_above_int32_max_rejected(collection):
    """Test killOp rejects a double above the int32 range."""
    result = execute_admin_command(collection, {"killOp": 1, "op": float(INT32_OVERFLOW)})
    assertFailureCode(
        result,
        KILLOP_OPID_NOT_INT32_ERROR,
        msg="killOp should reject an op value outside the int32 range",
    )


def test_killOp_op_long_above_int32_max_rejected(collection):
    """Test killOp rejects a long above the int32 range."""
    result = execute_admin_command(collection, {"killOp": 1, "op": Int64(INT32_OVERFLOW)})
    assertFailureCode(
        result,
        KILLOP_OPID_NOT_INT32_ERROR,
        msg="killOp should reject an op value outside the int32 range",
    )


def test_killOp_op_long_below_int32_min_rejected(collection):
    """Test killOp rejects a long below the int32 range."""
    result = execute_admin_command(collection, {"killOp": 1, "op": Int64(INT32_UNDERFLOW)})
    assertFailureCode(
        result,
        KILLOP_OPID_NOT_INT32_ERROR,
        msg="killOp should reject an op value outside the int32 range",
    )


def test_killOp_op_int64_max_rejected(collection):
    """Test killOp rejects INT64_MAX (outside the int32 range)."""
    result = execute_admin_command(collection, {"killOp": 1, "op": INT64_MAX})
    assertFailureCode(
        result,
        KILLOP_OPID_NOT_INT32_ERROR,
        msg="killOp should reject an op value outside the int32 range",
    )


def test_killOp_op_int64_min_rejected(collection):
    """Test killOp rejects INT64_MIN (outside the int32 range)."""
    result = execute_admin_command(collection, {"killOp": 1, "op": INT64_MIN})
    assertFailureCode(
        result,
        KILLOP_OPID_NOT_INT32_ERROR,
        msg="killOp should reject an op value outside the int32 range",
    )


def test_killOp_op_decimal_above_int32_max_rejected(collection):
    """Test killOp rejects a decimal above the int32 range."""
    result = execute_admin_command(collection, {"killOp": 1, "op": Decimal128(str(INT32_OVERFLOW))})
    assertFailureCode(
        result,
        KILLOP_OPID_NOT_INT32_ERROR,
        msg="killOp should reject an op value outside the int32 range",
    )


def test_killOp_on_non_admin_database_fails(collection):
    """Test killOp run against non-admin database fails with error."""
    result = execute_command(collection, {"killOp": 1, "op": NON_RUNNING_OP_ID})
    assertFailureCode(result, UNAUTHORIZED_ERROR, msg="Should fail on non-admin database")


def test_killOp_missing_op_field(collection):
    """Test killOp without op field fails with error."""
    result = execute_admin_command(collection, {"killOp": 1})
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="Should fail without op field")
