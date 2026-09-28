"""Tests for serverStatus command core behavior.

Validates semantic correctness of response field values, non-negative
counters, and cross-field consistency.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt, Gte

pytestmark = pytest.mark.admin


# Property [Positive Values]: serverStatus fields have expected positive or non-negative bounds.
POSITIVE_VALUE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="uptime_gte_0",
        checks={"uptime": Gte(0)},
        msg="serverStatus should return uptime >= 0",
    ),
    DiagnosticTestCase(
        id="uptimeMillis_gte_0",
        checks={"uptimeMillis": Gte(0)},
        msg="serverStatus should return uptimeMillis >= 0",
    ),
    DiagnosticTestCase(
        id="uptimeEstimate_gte_0",
        checks={"uptimeEstimate": Gte(0)},
        msg="serverStatus should return uptimeEstimate >= 0",
    ),
    DiagnosticTestCase(
        id="pid_gt_0",
        checks={"pid": Gt(0)},
        msg="serverStatus should return pid > 0",
    ),
    DiagnosticTestCase(
        id="connections_current_gte_1",
        checks={"connections.current": Gte(1)},
        msg="serverStatus should report at least one current connection",
    ),
    DiagnosticTestCase(
        id="connections_available_gte_0",
        checks={"connections.available": Gte(0)},
        msg="serverStatus should return connections.available >= 0",
    ),
    DiagnosticTestCase(
        id="connections_totalCreated_gte_1",
        checks={"connections.totalCreated": Gte(1)},
        msg="serverStatus should report at least one created connection",
    ),
    DiagnosticTestCase(
        id="mem_resident_gt_0",
        checks={"mem.resident": Gt(0)},
        msg="serverStatus should report positive resident memory usage",
    ),
    DiagnosticTestCase(
        id="mem_virtual_gt_0",
        checks={"mem.virtual": Gt(0)},
        msg="serverStatus should report positive virtual memory usage",
    ),
    DiagnosticTestCase(
        id="globalLock_totalTime_gte_0",
        checks={"globalLock.totalTime": Gte(0)},
        msg="serverStatus should return globalLock.totalTime >= 0",
    ),
    DiagnosticTestCase(
        id="process_is_mongod",
        checks={"process": Eq("mongod")},
        msg="serverStatus should return process as mongod on a mongod instance",
    ),
]

# Property [Non-Negative Counters]: serverStatus counter fields are non-negative integers.
COUNTER_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="asserts_regular_gte_0",
        checks={"asserts.regular": Gte(0)},
        msg="serverStatus should return asserts.regular >= 0",
    ),
    DiagnosticTestCase(
        id="asserts_warning_gte_0",
        checks={"asserts.warning": Gte(0)},
        msg="serverStatus should return asserts.warning >= 0",
    ),
    DiagnosticTestCase(
        id="asserts_msg_gte_0",
        checks={"asserts.msg": Gte(0)},
        msg="serverStatus should return asserts.msg >= 0",
    ),
    DiagnosticTestCase(
        id="asserts_user_gte_0",
        checks={"asserts.user": Gte(0)},
        msg="serverStatus should return asserts.user >= 0",
    ),
    DiagnosticTestCase(
        id="asserts_rollovers_gte_0",
        checks={"asserts.rollovers": Gte(0)},
        msg="serverStatus should return asserts.rollovers >= 0",
    ),
    DiagnosticTestCase(
        id="opcounters_insert_gte_0",
        checks={"opcounters.insert": Gte(0)},
        msg="serverStatus should return opcounters.insert >= 0",
    ),
    DiagnosticTestCase(
        id="opcounters_query_gte_0",
        checks={"opcounters.query": Gte(0)},
        msg="serverStatus should return opcounters.query >= 0",
    ),
    DiagnosticTestCase(
        id="opcounters_update_gte_0",
        checks={"opcounters.update": Gte(0)},
        msg="serverStatus should return opcounters.update >= 0",
    ),
    DiagnosticTestCase(
        id="opcounters_delete_gte_0",
        checks={"opcounters.delete": Gte(0)},
        msg="serverStatus should return opcounters.delete >= 0",
    ),
    DiagnosticTestCase(
        id="opcounters_getmore_gte_0",
        checks={"opcounters.getmore": Gte(0)},
        msg="serverStatus should return opcounters.getmore >= 0",
    ),
    DiagnosticTestCase(
        id="opcounters_command_gte_0",
        checks={"opcounters.command": Gte(0)},
        msg="serverStatus should return opcounters.command >= 0",
    ),
    DiagnosticTestCase(
        id="network_bytesIn_gte_0",
        checks={"network.bytesIn": Gte(0)},
        msg="serverStatus should return network.bytesIn >= 0",
    ),
    DiagnosticTestCase(
        id="network_bytesOut_gte_0",
        checks={"network.bytesOut": Gte(0)},
        msg="serverStatus should return network.bytesOut >= 0",
    ),
    DiagnosticTestCase(
        id="network_numRequests_gte_0",
        checks={"network.numRequests": Gte(0)},
        msg="serverStatus should return network.numRequests >= 0",
    ),
    DiagnosticTestCase(
        id="catalogStats_collections_gte_0",
        checks={"catalogStats.collections": Gte(0)},
        msg="serverStatus should return catalogStats.collections >= 0",
    ),
    DiagnosticTestCase(
        id="catalogStats_capped_gte_0",
        checks={"catalogStats.capped": Gte(0)},
        msg="serverStatus should return catalogStats.capped >= 0",
    ),
    DiagnosticTestCase(
        id="catalogStats_views_gte_0",
        checks={"catalogStats.views": Gte(0)},
        msg="serverStatus should return catalogStats.views >= 0",
    ),
]

VALUE_BOUND_TESTS = POSITIVE_VALUE_TESTS + COUNTER_TESTS


@pytest.mark.parametrize("test", pytest_params(VALUE_BOUND_TESTS))
def test_serverStatus_value_bounds(collection, test):
    """Verifies serverStatus fields have expected value bounds."""
    result = execute_admin_command(collection, {"serverStatus": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Cross-Field Consistency]: serverStatus fields are consistent across calls.


def test_serverStatus_totalCreated_gte_current(collection):
    """Verify serverStatus connections.totalCreated >= connections.current."""
    result = execute_admin_command(collection, {"serverStatus": 1})
    current = result["connections"]["current"]
    assertProperties(
        result,
        {"connections.totalCreated": Gte(current)},
        raw_res=True,
        msg="serverStatus should report totalCreated >= current connections",
    )


def test_serverStatus_uptimeMillis_consistent_with_uptime(collection):
    """Verify serverStatus uptime is consistent with uptimeMillis."""
    result = execute_admin_command(collection, {"serverStatus": 1})
    uptime_from_millis = result["uptimeMillis"] // 1000
    assertProperties(
        result,
        {"uptime": Gte(uptime_from_millis - 1)},
        raw_res=True,
        msg="serverStatus should return uptime >= uptimeMillis / 1000 (within 1s tolerance)",
    )


def test_serverStatus_pid_consistent_across_calls(collection):
    """Verify serverStatus pid is stable across calls."""
    result1 = execute_admin_command(collection, {"serverStatus": 1})
    result2 = execute_admin_command(collection, {"serverStatus": 1})
    assertProperties(
        result2,
        {"pid": Eq(result1["pid"])},
        raw_res=True,
        msg="serverStatus should return the same pid across calls",
    )


def test_serverStatus_host_consistent_across_calls(collection):
    """Verify serverStatus host is stable across calls."""
    result1 = execute_admin_command(collection, {"serverStatus": 1})
    result2 = execute_admin_command(collection, {"serverStatus": 1})
    assertProperties(
        result2,
        {"host": Eq(result1["host"])},
        raw_res=True,
        msg="serverStatus should return the same host across calls",
    )


def test_serverStatus_version_consistent_across_calls(collection):
    """Verify serverStatus version is stable across calls."""
    result1 = execute_admin_command(collection, {"serverStatus": 1})
    result2 = execute_admin_command(collection, {"serverStatus": 1})
    assertProperties(
        result2,
        {"version": Eq(result1["version"])},
        raw_res=True,
        msg="serverStatus should return the same version across calls",
    )


def test_serverStatus_cross_database_same_core_fields(collection):
    """Verify serverStatus core identity fields match across databases."""
    admin_result = execute_admin_command(collection, {"serverStatus": 1})
    db_result = execute_command(collection, {"serverStatus": 1})
    assertProperties(
        db_result,
        {
            "host": Eq(admin_result["host"]),
            "version": Eq(admin_result["version"]),
            "process": Eq(admin_result["process"]),
            "pid": Eq(admin_result["pid"]),
        },
        raw_res=True,
        msg="serverStatus should return the same core fields regardless of database",
    )
