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
    """Read the current FCV."""
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
    """Test writeConcern as object is accepted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": 5000},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="writeConcern as object should be accepted")


def test_setFeatureCompatibilityVersion_writeConcern_empty_object_accepted(collection):
    """Test writeConcern = {} (empty doc) is accepted with defaults applied."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="writeConcern = {} should be accepted")


def test_setFeatureCompatibilityVersion_writeConcern_null_as_omitted(collection):
    """Test writeConcern = null is treated as omitted (accepted)."""
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
        result, {"ok": 1.0}, msg="writeConcern = null should be treated as omitted"
    )


def test_setFeatureCompatibilityVersion_writeConcern_string_rejected(collection):
    """Test writeConcern as string fails with TYPE_MISMATCH_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": "majority",
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="writeConcern as string should be rejected")


def test_setFeatureCompatibilityVersion_writeConcern_int_rejected(collection):
    """Test writeConcern as int fails with TYPE_MISMATCH_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": 1,
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="writeConcern as int should be rejected")


def test_setFeatureCompatibilityVersion_writeConcern_bool_rejected(collection):
    """Test writeConcern as bool fails with TYPE_MISMATCH_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": True,
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="writeConcern as bool should be rejected")


def test_setFeatureCompatibilityVersion_writeConcern_array_rejected(collection):
    """Test writeConcern as array fails with TYPE_MISMATCH_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": [{"w": 1}],
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="writeConcern as array should be rejected")


def test_setFeatureCompatibilityVersion_writeConcern_long_rejected(collection):
    """Test writeConcern as long fails with TYPE_MISMATCH_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": Int64(1),
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="writeConcern as long should be rejected")


def test_setFeatureCompatibilityVersion_writeConcern_double_rejected(collection):
    """Test writeConcern as double fails with TYPE_MISMATCH_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": 1.0,
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="writeConcern as double should be rejected")


def test_setFeatureCompatibilityVersion_writeConcern_decimal_rejected(collection):
    """Test writeConcern as decimal128 fails with TYPE_MISMATCH_ERROR."""
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
        result, TYPE_MISMATCH_ERROR, msg="writeConcern as decimal128 should be rejected"
    )


def test_setFeatureCompatibilityVersion_omitting_writeConcern_succeeds(collection):
    """Test omitting writeConcern still succeeds (default wtimeout applied)."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": True},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Omitting writeConcern should succeed")


def test_setFeatureCompatibilityVersion_wtimeout_double_coercion(collection):
    """Test writeConcern.wtimeout as whole-number double (5000.0) is accepted."""
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
        result, {"ok": 1.0}, msg="wtimeout as whole-number double should be accepted"
    )


def test_setFeatureCompatibilityVersion_wtimeout_long_coercion(collection):
    """Test writeConcern.wtimeout as Int64 is accepted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": Int64(5000)},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="wtimeout as Int64 should be accepted")


def test_setFeatureCompatibilityVersion_wtimeout_decimal_whole_coercion(collection):
    """Test writeConcern.wtimeout as whole-number Decimal128 coercion."""
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
        result, {"ok": 1.0}, msg="wtimeout as whole-number Decimal128 should be accepted"
    )


def test_setFeatureCompatibilityVersion_wtimeout_fractional_double_accepted(collection):
    """Test writeConcern.wtimeout as fractional double (5000.5) is accepted."""
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
        result, {"ok": 1.0}, msg="wtimeout as fractional double should be accepted"
    )


def test_setFeatureCompatibilityVersion_wtimeout_negative_value_accepted(collection):
    """Test writeConcern.wtimeout as negative value (-1) is accepted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": -1},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="wtimeout as negative value should be accepted")
