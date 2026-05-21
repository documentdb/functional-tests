"""Tests for buildInfo command response structure.

Validates presence, types, and values of stable and unstable response fields.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, Exists, Gte, IsType, Len

pytestmark = pytest.mark.admin


# --- Stable Fields: Presence and Types ---


def test_buildInfo_version_is_string(collection):
    """Test response contains 'version' field with type string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"version": IsType("string")}, raw_res=True)


def test_buildInfo_gitVersion_is_string(collection):
    """Test response contains 'gitVersion' field with type string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"gitVersion": IsType("string")}, raw_res=True)


def test_buildInfo_versionArray_is_array(collection):
    """Test response contains 'versionArray' field with type array."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"versionArray": IsType("array")}, raw_res=True)


def test_buildInfo_storageEngines_is_array(collection):
    """Test response contains 'storageEngines' field with type array."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"storageEngines": IsType("array")}, raw_res=True)


def test_buildInfo_javascriptEngine_is_string(collection):
    """Test response contains 'javascriptEngine' field with type string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"javascriptEngine": IsType("string")}, raw_res=True)


def test_buildInfo_bits_is_int(collection):
    """Test response contains 'bits' field with type int."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"bits": IsType("int")}, raw_res=True)


def test_buildInfo_debug_is_bool(collection):
    """Test response contains 'debug' field with type boolean."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"debug": IsType("bool")}, raw_res=True)


def test_buildInfo_maxBsonObjectSize_exists(collection):
    """Test response contains 'maxBsonObjectSize' field."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"maxBsonObjectSize": Exists()}, raw_res=True)


def test_buildInfo_openssl_is_object(collection):
    """Test response contains 'openssl' field with type object."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"openssl": IsType("object")}, raw_res=True)


def test_buildInfo_ok_is_1(collection):
    """Test response contains 'ok' field with value 1.0."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"ok": Eq(1.0)}, raw_res=True)


# --- Stable Fields: Value Validation ---


def test_buildInfo_versionArray_has_4_elements(collection):
    """Test 'versionArray' has exactly 4 elements."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"versionArray": Len(4)}, raw_res=True)


def test_buildInfo_versionArray_elements_nonneg(collection):
    """Test 'versionArray' elements are non-negative integers."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(
        result,
        {
            "versionArray.0": Gte(0),
            "versionArray.1": Gte(0),
            "versionArray.2": Gte(0),
            "versionArray.3": Gte(0),
        },
        raw_res=True,
    )


def test_buildInfo_versionArray_matches_version_major(collection):
    """Test versionArray[0] matches major version from version string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(
        result,
        {"versionArray.0": Eq(int(result["version"].split(".")[0]))},
        raw_res=True,
    )


def test_buildInfo_versionArray_matches_version_minor(collection):
    """Test versionArray[1] matches minor version from version string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(
        result,
        {"versionArray.1": Eq(int(result["version"].split(".")[1]))},
        raw_res=True,
    )


def test_buildInfo_versionArray_matches_version_patch(collection):
    """Test versionArray[2] matches patch version from version string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(
        result,
        {"versionArray.2": Eq(int(result["version"].split(".")[2].split("-")[0]))},
        raw_res=True,
    )


def test_buildInfo_bits_is_64(collection):
    """Test 'bits' is 64 for modern deployments."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"bits": Eq(64)}, raw_res=True)


def test_buildInfo_maxBsonObjectSize_is_16mb(collection):
    """Test 'maxBsonObjectSize' is 16777216 (16 MB)."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"maxBsonObjectSize": Eq(Int64(16777216))}, raw_res=True)


# --- openssl Sub-Document ---


def test_buildInfo_openssl_running_is_string(collection):
    """Test 'openssl.running' field is a string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"openssl": {"running": IsType("string")}}, raw_res=True)


def test_buildInfo_openssl_running_exists(collection):
    """Test 'openssl.running' field exists."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"openssl": {"running": Exists()}}, raw_res=True)


# --- Unstable/Optional Fields ---


def test_buildInfo_allocator_is_string_if_present(collection):
    """Test 'allocator' field is string if present."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"allocator": IsType("string")}, raw_res=True)


def test_buildInfo_buildEnvironment_is_object_if_present(collection):
    """Test 'buildEnvironment' field is object if present."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"buildEnvironment": IsType("object")}, raw_res=True)


def test_buildInfo_modules_is_array_if_present(collection):
    """Test 'modules' field is array if present."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, {"modules": IsType("array")}, raw_res=True)
