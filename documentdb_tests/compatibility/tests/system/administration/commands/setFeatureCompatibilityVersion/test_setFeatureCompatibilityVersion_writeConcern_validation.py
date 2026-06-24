"""Tests for setFeatureCompatibilityVersion writeConcern field validation.

Validates writeConcern type validation, null-as-omitted behavior,
empty-doc acceptance, and wtimeout coercion.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
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


def test_setFeatureCompatibilityVersion_writeConcern_object_accepted(collection):
    """Test setFeatureCompatibilityVersion accepts writeConcern as object."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": 5000},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept writeConcern as object",
    )


def test_setFeatureCompatibilityVersion_writeConcern_empty_object_accepted(collection):
    """Test setFeatureCompatibilityVersion accepts writeConcern as empty object."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept writeConcern as empty object",
    )


def test_setFeatureCompatibilityVersion_writeConcern_null_as_omitted(collection):
    """Test setFeatureCompatibilityVersion treats writeConcern=null as omitted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": None,
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should treat writeConcern=null as omitted",
    )


def test_setFeatureCompatibilityVersion_writeConcern_string_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects writeConcern as string."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": "majority",
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as string",
    )


def test_setFeatureCompatibilityVersion_writeConcern_int_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects writeConcern as int."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": 1,
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as int",
    )


def test_setFeatureCompatibilityVersion_writeConcern_bool_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects writeConcern as bool."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": True,
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as bool",
    )


def test_setFeatureCompatibilityVersion_writeConcern_array_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects writeConcern as array."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": [{"w": 1}],
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as array",
    )


def test_setFeatureCompatibilityVersion_writeConcern_long_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects writeConcern as long."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": Int64(1),
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as long",
    )


def test_setFeatureCompatibilityVersion_writeConcern_double_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects writeConcern as double."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": 1.0,
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as double",
    )


def test_setFeatureCompatibilityVersion_writeConcern_decimal_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects writeConcern as Decimal128."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": Decimal128("1"),
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as Decimal128",
    )


def test_setFeatureCompatibilityVersion_omitting_writeConcern_succeeds(collection):
    """Test setFeatureCompatibilityVersion succeeds when writeConcern is omitted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": True},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when writeConcern is omitted",
    )


def test_setFeatureCompatibilityVersion_wtimeout_double_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts wtimeout as whole-number double."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": 5000.0},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as whole-number double",
    )


def test_setFeatureCompatibilityVersion_wtimeout_long_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts wtimeout as Int64."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": Int64(5000)},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as Int64",
    )


def test_setFeatureCompatibilityVersion_wtimeout_decimal_whole_coercion(collection):
    """Test setFeatureCompatibilityVersion accepts wtimeout as whole-number Decimal128."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": Decimal128("5000")},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as whole-number Decimal128",
    )


def test_setFeatureCompatibilityVersion_wtimeout_fractional_double_accepted(collection):
    """Test setFeatureCompatibilityVersion accepts wtimeout as fractional double."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": 5000.5},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as fractional double",
    )


def test_setFeatureCompatibilityVersion_wtimeout_negative_value_accepted(collection):
    """Test setFeatureCompatibilityVersion accepts wtimeout as negative value."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": -1},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as negative value",
    )
