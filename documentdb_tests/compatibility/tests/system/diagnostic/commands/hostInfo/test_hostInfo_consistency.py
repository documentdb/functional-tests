"""Tests for hostInfo core behavior and consistency.

Validates that hostInfo returns the expected top-level structure, is stable
across repeated calls, ignores its argument value, runs on any database, and
that system.currentTime advances between calls. Also cross-checks that
system.cpuAddrSize agrees with buildInfo.bits.

Spec categories: rule_specs "Core Behavior", "Consistency";
hostinfo_js_specs "CPU address size consistency".
"""

import time

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.property_checks import Eq, Exists, Gt

pytestmark = pytest.mark.admin


def test_hostInfo_returns_system_os_extra(collection):
    """Verify hostInfo returns a document with system, os, and extra fields."""
    result = execute_admin_command(collection, {"hostInfo": 1})
    assertProperties(
        result,
        {"ok": Eq(1.0), "system": Exists(), "os": Exists(), "extra": Exists()},
        raw_res=True,
        msg="hostInfo should return ok:1 with system, os, and extra documents",
    )


def test_hostInfo_idempotent_static_fields(collection):
    """Verify static system/os fields are identical across repeated calls."""
    first = execute_admin_command(collection, {"hostInfo": 1})
    second = execute_admin_command(collection, {"hostInfo": 1})
    assertProperties(
        second,
        {
            "system.hostname": Eq(first["system"]["hostname"]),
            "system.cpuArch": Eq(first["system"]["cpuArch"]),
            "system.cpuAddrSize": Eq(first["system"]["cpuAddrSize"]),
            "system.numCores": Eq(first["system"]["numCores"]),
            "system.memSizeMB": Eq(first["system"]["memSizeMB"]),
            "os": Eq(first["os"]),
        },
        raw_res=True,
        msg="Static host fields should be stable across calls",
    )


def test_hostInfo_argument_value_ignored(collection):
    """Verify the command value does not affect the os/extra output."""
    numeric = execute_admin_command(collection, {"hostInfo": 1})
    other = execute_admin_command(collection, {"hostInfo": "ignored"})
    assertProperties(
        other,
        {"os": Eq(numeric["os"]), "extra": Eq(numeric["extra"])},
        raw_res=True,
        msg="hostInfo output should not depend on the command value",
    )


def test_hostInfo_currentTime_advances(collection):
    """Verify system.currentTime advances between successive calls (is dynamic)."""
    first = execute_admin_command(collection, {"hostInfo": 1})
    time.sleep(0.1)
    second = execute_admin_command(collection, {"hostInfo": 1})
    assertProperties(
        second,
        {"system.currentTime": Gt(first["system"]["currentTime"])},
        raw_res=True,
        msg="system.currentTime should advance between calls",
    )


def test_hostInfo_succeeds_on_non_admin_database(collection):
    """Verify hostInfo succeeds when run on a non-admin database (auth disabled)."""
    result = execute_command(collection, {"hostInfo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed on a non-admin database")


def test_hostInfo_cpuAddrSize_matches_buildInfo_bits(collection):
    """Verify system.cpuAddrSize equals buildInfo.bits."""
    build_info = execute_admin_command(collection, {"buildInfo": 1})
    host_info = execute_admin_command(collection, {"hostInfo": 1})
    assertProperties(
        host_info,
        {"system.cpuAddrSize": Eq(build_info["bits"])},
        raw_res=True,
        msg="hostInfo system.cpuAddrSize should match buildInfo bits",
    )
