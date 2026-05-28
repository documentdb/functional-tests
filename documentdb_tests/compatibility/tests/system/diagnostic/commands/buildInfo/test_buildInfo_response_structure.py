"""Tests for buildInfo command response structure.

Validates presence, types, and values of response fields.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Gte, IsType, Len

pytestmark = pytest.mark.admin


PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="version_is_string",
        checks={"version": IsType("string")},
        msg="'version' field should be a string",
    ),
    DiagnosticTestCase(
        id="gitVersion_is_string",
        checks={"gitVersion": IsType("string")},
        msg="'gitVersion' field should be a string",
    ),
    DiagnosticTestCase(
        id="versionArray_is_array",
        checks={"versionArray": IsType("array")},
        msg="'versionArray' field should be an array",
    ),
    DiagnosticTestCase(
        id="storageEngines_is_array",
        checks={"storageEngines": IsType("array")},
        msg="'storageEngines' field should be an array",
    ),
    DiagnosticTestCase(
        id="javascriptEngine_is_string",
        checks={"javascriptEngine": IsType("string")},
        msg="'javascriptEngine' field should be a string",
    ),
    DiagnosticTestCase(
        id="bits_is_int",
        checks={"bits": IsType("int")},
        msg="'bits' field should be an int",
    ),
    DiagnosticTestCase(
        id="debug_is_bool",
        checks={"debug": IsType("bool")},
        msg="'debug' field should be a bool",
    ),
    DiagnosticTestCase(
        id="maxBsonObjectSize_exists",
        checks={"maxBsonObjectSize": Exists()},
        msg="'maxBsonObjectSize' field should exist",
    ),
    DiagnosticTestCase(
        id="openssl_is_object",
        checks={"openssl": IsType("object")},
        msg="'openssl' field should be an object",
    ),
    DiagnosticTestCase(
        id="ok_is_1",
        checks={"ok": Eq(1.0)},
        msg="'ok' field should be 1.0",
    ),
    DiagnosticTestCase(
        id="versionArray_has_4_elements",
        checks={"versionArray": Len(4)},
        msg="'versionArray' should have exactly 4 elements",
    ),
    DiagnosticTestCase(
        id="versionArray_elements_nonneg",
        checks={
            "versionArray.0": Gte(0),
            "versionArray.1": Gte(0),
            "versionArray.2": Gte(0),
            "versionArray.3": Gte(0),
        },
        msg="'versionArray' elements should be non-negative",
    ),
    DiagnosticTestCase(
        id="maxBsonObjectSize_gte_16mb",
        checks={"maxBsonObjectSize": Gte(16777216)},
        msg="'maxBsonObjectSize' should be at least 16777216 (16 MB)",
    ),
    DiagnosticTestCase(
        id="modules_is_array",
        checks={"modules": IsType("array")},
        msg="'modules' field should be an array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_buildInfo_response_properties(collection, test):
    """Verifies buildInfo response fields have expected types and values."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_buildInfo_versionArray_matches_version_string(collection):
    """Verify versionArray[0..2] matches major.minor.patch from version string."""
    result = execute_admin_command(collection, {"buildInfo": 1})
    parts = result["version"].split(".")
    assertProperties(
        result,
        {
            "versionArray.0": Eq(int(parts[0])),
            "versionArray.1": Eq(int(parts[1])),
            "versionArray.2": Eq(int(parts[2].split("-")[0])),
        },
        raw_res=True,
        msg="versionArray should match version string",
    )
