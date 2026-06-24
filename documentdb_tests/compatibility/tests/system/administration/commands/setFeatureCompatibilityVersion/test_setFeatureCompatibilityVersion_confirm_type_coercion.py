"""Tests for setFeatureCompatibilityVersion confirm field type coercion.

Validates how the confirm field handles various BSON types beyond bool,
recording coercion behavior (accepted-as-true vs rejected/treated-as-false).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import FCV_CONFIRM_REQUIRED_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection):
    """Read the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return "8.2"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.2")
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
    """Test setFeatureCompatibilityVersion accepts confirm=1 (int32) as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 1}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=1 (int) as true",
    )
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_int_0_coercion(collection):
    """Test setFeatureCompatibilityVersion treats confirm=0 (int32) as false."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 0}
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=0 as false",
    )


def test_setFeatureCompatibilityVersion_confirm_double_1_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts confirm=1.0 (double) as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 1.0}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=1.0 (double) as true",
    )
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_double_0_coercion(collection):
    """Test setFeatureCompatibilityVersion treats confirm=0.0 (double) as false."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": 0.0}
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=0.0 as false",
    )


def test_setFeatureCompatibilityVersion_confirm_long_1_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts confirm=Int64(1) as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": Int64(1)}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=Int64(1) as true",
    )
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_long_0_coercion(collection):
    """Test setFeatureCompatibilityVersion treats confirm=Int64(0) as false."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": Int64(0)}
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=Int64(0) as false",
    )


def test_setFeatureCompatibilityVersion_confirm_decimal_1_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts confirm=Decimal128('1') as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": target, "confirm": Decimal128("1")},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=Decimal128('1') as true",
    )
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_decimal_0_coercion(collection):
    """Test setFeatureCompatibilityVersion treats confirm=Decimal128('0') as false."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": target, "confirm": Decimal128("0")},
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=Decimal128('0') as false",
    )


def test_setFeatureCompatibilityVersion_confirm_null_coercion(collection):
    """Test setFeatureCompatibilityVersion treats confirm=null as not-true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": None}
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=null as not-true",
    )


def test_setFeatureCompatibilityVersion_confirm_negative_zero_coercion(collection):
    """Test setFeatureCompatibilityVersion treats confirm=-0.0 as false."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": -0.0}
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=-0.0 as false",
    )


def test_setFeatureCompatibilityVersion_confirm_nan_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts confirm=NaN as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": target, "confirm": float("nan")},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=NaN as true",
    )
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_infinity_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts confirm=Infinity as true."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": target, "confirm": float("inf")},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=Infinity as true",
    )
    _set_fcv(collection, current)


def test_setFeatureCompatibilityVersion_confirm_string_coercion(collection):
    """Test setFeatureCompatibilityVersion rejects confirm='true' (string)."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": "true"}
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as string type",
    )


def test_setFeatureCompatibilityVersion_confirm_object_coercion(collection):
    """Test setFeatureCompatibilityVersion rejects confirm as object."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": target, "confirm": {"a": 1}},
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as object type",
    )


def test_setFeatureCompatibilityVersion_confirm_array_coercion(collection):
    """Test setFeatureCompatibilityVersion rejects confirm as array."""
    current = _get_fcv(collection)
    target = _get_other_fcv(current)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": target, "confirm": [True]},
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as array type",
    )
