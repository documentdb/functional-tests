"""Tests for setFeatureCompatibilityVersion confirm field type coercion.

Validates how the confirm field handles various BSON types beyond bool,
recording coercion behavior (accepted-as-true vs rejected/treated-as-false).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

# Error code when confirm is treated as falsy (not-true)
FCV_CONFIRM_REQUIRED_ERROR = 7369100


def _get_fcv(collection):
    """Read the current FCV."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return "8.0"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.0")
    return str(fcv_data)


def _set_fcv(collection, version):
    """Set FCV with confirm:true."""
    return execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": version, "confirm": True}
    )


def _get_other_fcv(current):
    """Get a different supported FCV than the current one."""
    return "8.0" if current != "8.0" else "8.2"


def test_setFeatureCompatibilityVersion_confirm_int_1_coercion(collection):
    """Test confirm = 1 (int32) is accepted as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 1}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="confirm=1 (int) should be accepted as true")
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_int_0_coercion(collection):
    """Test confirm = 0 (int32) is treated as false (error 7369100)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 0}
    )
    assertFailureCode(
        result, FCV_CONFIRM_REQUIRED_ERROR, msg="confirm=0 should be treated as false"
    )


def test_setFeatureCompatibilityVersion_confirm_double_1_coercion(collection):
    """Test confirm = 1.0 (double) is accepted as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 1.0}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="confirm=1.0 (double) should be accepted as true")
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_double_0_coercion(collection):
    """Test confirm = 0.0 (double) is treated as false (error 7369100)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 0.0}
    )
    assertFailureCode(
        result, FCV_CONFIRM_REQUIRED_ERROR, msg="confirm=0.0 should be treated as false"
    )


def test_setFeatureCompatibilityVersion_confirm_long_1_coercion(collection):
    """Test confirm = Int64(1) is accepted as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": Int64(1)}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="confirm=Int64(1) should be accepted as true")
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_long_0_coercion(collection):
    """Test confirm = Int64(0) is treated as false (error 7369100)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": Int64(0)}
    )
    assertFailureCode(
        result, FCV_CONFIRM_REQUIRED_ERROR, msg="confirm=Int64(0) should be treated as false"
    )


def test_setFeatureCompatibilityVersion_confirm_decimal_1_coercion(collection):
    """Test confirm = Decimal128('1') is accepted as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": Decimal128("1")}
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="confirm=Decimal128('1') should be accepted as true"
    )
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_decimal_0_coercion(collection):
    """Test confirm = Decimal128('0') is treated as false (error 7369100)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": Decimal128("0")}
    )
    assertFailureCode(
        result, FCV_CONFIRM_REQUIRED_ERROR, msg="confirm=Decimal128('0') should be treated as false"
    )


def test_setFeatureCompatibilityVersion_confirm_null_coercion(collection):
    """Test confirm = null is treated as not-true (error 7369100)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": None}
    )
    assertFailureCode(
        result, FCV_CONFIRM_REQUIRED_ERROR, msg="confirm=null should be treated as not-true"
    )


def test_setFeatureCompatibilityVersion_confirm_negative_zero_coercion(collection):
    """Test confirm = -0.0 is treated as false (error 7369100)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": -0.0}
    )
    assertFailureCode(
        result, FCV_CONFIRM_REQUIRED_ERROR, msg="confirm=-0.0 should be treated as false"
    )


def test_setFeatureCompatibilityVersion_confirm_nan_coercion(collection):
    """Test confirm = NaN is accepted as true (truthy in MongoDB bool coercion)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": float("nan")}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="confirm=NaN should be accepted as true")
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_infinity_coercion(collection):
    """Test confirm = Infinity is accepted as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": float("inf")}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="confirm=Infinity should be accepted as true")
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_string_coercion(collection):
    """Test confirm = string is rejected with TYPE_MISMATCH_ERROR."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": "true"}
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="confirm='true' (string) should be rejected with type mismatch",
    )


def test_setFeatureCompatibilityVersion_confirm_object_coercion(collection):
    """Test confirm = object is rejected with TYPE_MISMATCH_ERROR."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": {"a": 1}}
    )
    assertFailureCode(
        result, TYPE_MISMATCH_ERROR, msg="confirm={} (object) should be rejected with type mismatch"
    )


def test_setFeatureCompatibilityVersion_confirm_array_coercion(collection):
    """Test confirm = array is rejected with TYPE_MISMATCH_ERROR."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": [True]}
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="confirm=[True] (array) should be rejected with type mismatch",
    )
