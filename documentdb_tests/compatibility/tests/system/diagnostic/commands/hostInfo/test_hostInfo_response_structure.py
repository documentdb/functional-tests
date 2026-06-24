"""Tests for hostInfo command response structure.

Validates presence, types, and value constraints of the system, os, and extra
sub-documents returned by hostInfo.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Gt,
    Gte,
    IsType,
    NonEmptyStr,
)

pytestmark = pytest.mark.admin


PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="system_is_object",
        checks={"system": IsType("object")},
        msg="'system' should be an embedded document",
    ),
    DiagnosticTestCase(
        id="os_is_object",
        checks={"os": IsType("object")},
        msg="'os' should be an embedded document",
    ),
    DiagnosticTestCase(
        id="extra_is_object",
        checks={"extra": IsType("object")},
        msg="'extra' should be an embedded document",
    ),
    DiagnosticTestCase(
        id="system_currentTime_is_date",
        checks={"system.currentTime": IsType("date")},
        msg="'system.currentTime' should be a date",
    ),
    DiagnosticTestCase(
        id="system_hostname_nonempty",
        checks={"system.hostname": NonEmptyStr()},
        msg="'system.hostname' should be a non-empty string",
    ),
    DiagnosticTestCase(
        id="system_cpuAddrSize_positive",
        checks={"system.cpuAddrSize": Gt(0)},
        msg="'system.cpuAddrSize' should be greater than 0",
    ),
    DiagnosticTestCase(
        id="system_memLimitMB_positive",
        checks={"system.memLimitMB": Gt(0)},
        msg="'system.memLimitMB' should be greater than 0",
    ),
    DiagnosticTestCase(
        id="system_cpuArch_nonempty",
        checks={"system.cpuArch": NonEmptyStr()},
        msg="'system.cpuArch' should be a non-empty string",
    ),
    DiagnosticTestCase(
        id="system_numaEnabled_is_bool",
        checks={"system.numaEnabled": IsType("bool")},
        msg="'system.numaEnabled' should be a bool",
    ),
    DiagnosticTestCase(
        id="system_numPhysicalCores_positive",
        checks={"system.numPhysicalCores": Gt(0)},
        msg="'system.numPhysicalCores' should be greater than 0",
    ),
    DiagnosticTestCase(
        id="system_numCpuSockets_positive",
        checks={"system.numCpuSockets": Gt(0)},
        msg="'system.numCpuSockets' should be greater than 0",
    ),
    DiagnosticTestCase(
        id="system_numNumaNodes_positive",
        checks={"system.numNumaNodes": Gt(0)},
        msg="'system.numNumaNodes' should be greater than 0",
    ),
    DiagnosticTestCase(
        id="os_type_nonempty",
        checks={"os.type": NonEmptyStr()},
        msg="'os.type' should be a non-empty string",
    ),
    DiagnosticTestCase(
        id="os_name_is_string",
        checks={"os.name": IsType("string")},
        msg="'os.name' should be a string",
    ),
    DiagnosticTestCase(
        id="os_version_is_string",
        checks={"os.version": IsType("string")},
        msg="'os.version' should be a string",
    ),
    DiagnosticTestCase(
        id="extra_versionString_is_string",
        checks={"extra.versionString": IsType("string")},
        msg="'extra.versionString' should be a string",
    ),
    DiagnosticTestCase(
        id="extra_pageSize_positive",
        checks={"extra.pageSize": Gt(0)},
        msg="'extra.pageSize' should be greater than 0",
    ),
    DiagnosticTestCase(
        id="system_numCores_positive",
        checks={"system.numCores": Gte(1)},
        msg="'system.numCores' should be at least 1",
    ),
    DiagnosticTestCase(
        id="system_numCoresAvailableToProcess_gte_neg1",
        checks={"system.numCoresAvailableToProcess": Gte(-1)},
        msg="'system.numCoresAvailableToProcess' should be >= -1",
    ),
    DiagnosticTestCase(
        id="system_memSizeMB_positive",
        checks={"system.memSizeMB": Gt(0)},
        msg="'system.memSizeMB' should be greater than 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_hostInfo_response_properties(collection, test):
    """Verifies hostInfo response fields have expected types and values."""
    result = execute_admin_command(collection, {"hostInfo": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_hostInfo_memSizeMB_gte_memLimitMB(collection):
    """Verify system.memLimitMB does not exceed system.memSizeMB."""
    result = execute_admin_command(collection, {"hostInfo": 1})
    mem_limit = result.get("system", {}).get("memLimitMB")
    assertProperties(
        result,
        {"system.memSizeMB": Gte(mem_limit)},
        raw_res=True,
        msg="'system.memSizeMB' should be >= 'system.memLimitMB'",
    )


def test_hostInfo_extra_platform_specific_fields(collection):
    """Verify extra contains the OS-specific fields documented for the host platform."""
    result = execute_admin_command(collection, {"hostInfo": 1})
    os_type = result.get("os", {}).get("type")
    if os_type == "Linux":
        checks = {
            "extra.libcVersion": IsType("string"),
            "extra.kernelVersion": IsType("string"),
        }
    elif os_type == "Darwin":
        checks = {
            "extra.cpuString": IsType("string"),
        }
    else:
        pytest.skip(f"Unrecognized os.type {os_type!r}; platform-specific fields not asserted")
    assertProperties(
        result, checks, raw_res=True, msg=f"extra should match documented {os_type} fields"
    )
