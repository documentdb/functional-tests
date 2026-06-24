"""Tests for hostInfo command response structure.

Validates presence, types, and value constraints of the system, os, and extra
sub-documents returned by hostInfo.

Spec categories: rule_specs "Response Structure - system/os/extra",
"Field Presence (Platform-Dependent)", "Value Constraints";
hostinfo_js_specs "Response structure - OS/System fields";
host_info_chimera_js_specs "Minimal response fields" (verifiable subset).
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    Exists,
    Gt,
    Gte,
    IsType,
    NonEmptyStr,
    NotExists,
)

pytestmark = pytest.mark.admin


PROPERTY_TESTS: list[DiagnosticTestCase] = [
    # Top-level structure
    DiagnosticTestCase(
        id="ok_is_1",
        checks={"ok": IsType("double")},
        msg="'ok' field should be a double",
    ),
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
    # system fields
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
        id="system_cpuAddrSize_is_int",
        checks={"system.cpuAddrSize": IsType("int")},
        msg="'system.cpuAddrSize' should be an int",
    ),
    DiagnosticTestCase(
        id="system_memSizeMB_is_long",
        checks={"system.memSizeMB": IsType("long")},
        msg="'system.memSizeMB' should be a long",
    ),
    DiagnosticTestCase(
        id="system_memLimitMB_is_long",
        checks={"system.memLimitMB": IsType("long")},
        msg="'system.memLimitMB' should be a long",
    ),
    DiagnosticTestCase(
        id="system_numCores_is_int",
        checks={"system.numCores": IsType("int")},
        msg="'system.numCores' should be an int",
    ),
    DiagnosticTestCase(
        id="system_numCoresAvailableToProcess_is_int",
        checks={"system.numCoresAvailableToProcess": IsType("int")},
        msg="'system.numCoresAvailableToProcess' should be an int",
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
        id="system_numPhysicalCores_is_int",
        checks={"system.numPhysicalCores": IsType("int")},
        msg="'system.numPhysicalCores' should be an int",
    ),
    DiagnosticTestCase(
        id="system_numCpuSockets_is_int",
        checks={"system.numCpuSockets": IsType("int")},
        msg="'system.numCpuSockets' should be an int",
    ),
    DiagnosticTestCase(
        id="system_numNumaNodes_is_int",
        checks={"system.numNumaNodes": IsType("int")},
        msg="'system.numNumaNodes' should be an int",
    ),
    # os fields
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
    # extra fields (present on both Linux and macOS per the spec)
    DiagnosticTestCase(
        id="extra_versionString_is_string",
        checks={"extra.versionString": IsType("string")},
        msg="'extra.versionString' should be a string",
    ),
    DiagnosticTestCase(
        id="extra_pageSize_is_int",
        checks={"extra.pageSize": IsType("int")},
        msg="'extra.pageSize' should be an int",
    ),
    # Value ranges
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
    DiagnosticTestCase(
        id="extra_exists",
        checks={"extra": Exists()},
        msg="'extra' field should exist",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_hostInfo_response_properties(collection, test):
    """Verifies hostInfo response fields have expected types and values."""
    result = execute_admin_command(collection, {"hostInfo": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_hostInfo_cpuAddrSize_is_32_or_64(collection):
    """Verify system.cpuAddrSize is either 32 or 64 (the documented values)."""
    result = execute_admin_command(collection, {"hostInfo": 1})
    addr = result["system"]["cpuAddrSize"]
    # Map any out-of-set value to a sentinel so the equality check fails on it,
    # making the assertion pass only when cpuAddrSize is exactly 32 or 64.
    expected = addr if addr in (32, 64) else "__not_32_or_64__"
    assertProperties(
        result,
        {"system.cpuAddrSize": Eq(expected)},
        raw_res=True,
        msg=f"'system.cpuAddrSize' should be 32 or 64, got {addr!r}",
    )


def test_hostInfo_memLimitMB_lte_memSizeMB(collection):
    """Verify system.memLimitMB does not exceed system.memSizeMB."""
    result = execute_admin_command(collection, {"hostInfo": 1})
    mem_limit = result["system"]["memLimitMB"]
    assertProperties(
        result,
        {"system.memSizeMB": Gte(mem_limit)},
        raw_res=True,
        msg="'system.memSizeMB' should be >= 'system.memLimitMB'",
    )


def test_hostInfo_extra_platform_specific_fields(collection):
    """Verify extra contains the OS-specific fields documented for the host platform.

    Linux exposes libcVersion/kernelVersion (and not cpuString); macOS (Darwin)
    exposes cpuString (and not libcVersion/kernelVersion).
    """
    result = execute_admin_command(collection, {"hostInfo": 1})
    os_type = result["os"]["type"]
    if os_type == "Linux":
        checks = {
            "extra.libcVersion": IsType("string"),
            "extra.kernelVersion": IsType("string"),
            "extra.cpuString": NotExists(),
        }
    elif os_type == "Darwin":
        checks = {
            "extra.cpuString": IsType("string"),
            "extra.libcVersion": NotExists(),
            "extra.kernelVersion": NotExists(),
        }
    else:
        pytest.skip(f"Unrecognized os.type {os_type!r}; platform-specific fields not asserted")
    assertProperties(
        result, checks, raw_res=True, msg=f"extra should match documented {os_type} fields"
    )
