"""Tests for serverStatus command response structure.

Validates presence and types of core response fields, default sections,
and sub-document fields returned by serverStatus.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NonEmptyStr

pytestmark = pytest.mark.admin


# Property [Top-Level Fields]: serverStatus response contains core fields with expected types.
TOP_LEVEL_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="ok_is_1",
        checks={"ok": Eq(1.0)},
        msg="serverStatus should return ok: 1.0",
    ),
    DiagnosticTestCase(
        id="host_is_string",
        checks={"host": IsType("string")},
        msg="serverStatus should return host as a string",
    ),
    DiagnosticTestCase(
        id="version_is_string",
        checks={"version": IsType("string")},
        msg="serverStatus should return version as a string",
    ),
    DiagnosticTestCase(
        id="process_is_string",
        checks={"process": IsType("string")},
        msg="serverStatus should return process as a string",
    ),
    DiagnosticTestCase(
        id="pid_is_long",
        checks={"pid": IsType("long")},
        msg="serverStatus should return pid as a long",
    ),
    DiagnosticTestCase(
        id="uptime_is_double",
        checks={"uptime": IsType("double")},
        msg="serverStatus should return uptime as a double",
    ),
    DiagnosticTestCase(
        id="uptimeMillis_is_long",
        checks={"uptimeMillis": IsType("long")},
        msg="serverStatus should return uptimeMillis as a long",
    ),
    DiagnosticTestCase(
        id="uptimeEstimate_is_long",
        checks={"uptimeEstimate": IsType("long")},
        msg="serverStatus should return uptimeEstimate as a long",
    ),
    DiagnosticTestCase(
        id="localTime_is_date",
        checks={"localTime": IsType("date")},
        msg="serverStatus should return localTime as a date",
    ),
]

# Property [Default Sections]: serverStatus includes standard sections as objects by default.
DEFAULT_SECTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="asserts_is_object",
        checks={"asserts": IsType("object")},
        msg="serverStatus should include asserts as an object",
    ),
    DiagnosticTestCase(
        id="connections_is_object",
        checks={"connections": IsType("object")},
        msg="serverStatus should include connections as an object",
    ),
    DiagnosticTestCase(
        id="extra_info_is_object",
        checks={"extra_info": IsType("object")},
        msg="serverStatus should include extra_info as an object",
    ),
    DiagnosticTestCase(
        id="globalLock_is_object",
        checks={"globalLock": IsType("object")},
        msg="serverStatus should include globalLock as an object",
    ),
    DiagnosticTestCase(
        id="locks_is_object",
        checks={"locks": IsType("object")},
        msg="serverStatus should include locks as an object",
    ),
    DiagnosticTestCase(
        id="logicalSessionRecordCache_is_object",
        checks={"logicalSessionRecordCache": IsType("object")},
        msg="serverStatus should include logicalSessionRecordCache as an object",
    ),
    DiagnosticTestCase(
        id="mem_is_object",
        checks={"mem": IsType("object")},
        msg="serverStatus should include mem as an object",
    ),
    DiagnosticTestCase(
        id="metrics_is_object",
        checks={"metrics": IsType("object")},
        msg="serverStatus should include metrics as an object",
    ),
    DiagnosticTestCase(
        id="network_is_object",
        checks={"network": IsType("object")},
        msg="serverStatus should include network as an object",
    ),
    DiagnosticTestCase(
        id="opcounters_is_object",
        checks={"opcounters": IsType("object")},
        msg="serverStatus should include opcounters as an object",
    ),
    DiagnosticTestCase(
        id="opcountersRepl_is_object",
        checks={"opcountersRepl": IsType("object")},
        msg="serverStatus should include opcountersRepl as an object",
    ),
    DiagnosticTestCase(
        id="storageEngine_is_object",
        checks={"storageEngine": IsType("object")},
        msg="serverStatus should include storageEngine as an object",
    ),
    DiagnosticTestCase(
        id="transactions_is_object",
        checks={"transactions": IsType("object")},
        msg="serverStatus should include transactions as an object",
    ),
    DiagnosticTestCase(
        id="catalogStats_is_object",
        checks={"catalogStats": IsType("object")},
        msg="serverStatus should include catalogStats as an object",
    ),
]

# Property [Sub-Document Fields]: serverStatus sections contain expected nested fields.
SUB_DOC_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="asserts_regular_exists",
        checks={"asserts.regular": Exists()},
        msg="serverStatus should include asserts.regular",
    ),
    DiagnosticTestCase(
        id="asserts_warning_exists",
        checks={"asserts.warning": Exists()},
        msg="serverStatus should include asserts.warning",
    ),
    DiagnosticTestCase(
        id="asserts_msg_exists",
        checks={"asserts.msg": Exists()},
        msg="serverStatus should include asserts.msg",
    ),
    DiagnosticTestCase(
        id="asserts_user_exists",
        checks={"asserts.user": Exists()},
        msg="serverStatus should include asserts.user",
    ),
    DiagnosticTestCase(
        id="asserts_rollovers_exists",
        checks={"asserts.rollovers": Exists()},
        msg="serverStatus should include asserts.rollovers",
    ),
    DiagnosticTestCase(
        id="connections_current_exists",
        checks={"connections.current": Exists()},
        msg="serverStatus should include connections.current",
    ),
    DiagnosticTestCase(
        id="connections_available_exists",
        checks={"connections.available": Exists()},
        msg="serverStatus should include connections.available",
    ),
    DiagnosticTestCase(
        id="connections_totalCreated_exists",
        checks={"connections.totalCreated": Exists()},
        msg="serverStatus should include connections.totalCreated",
    ),
    DiagnosticTestCase(
        id="connections_active_exists",
        checks={"connections.active": Exists()},
        msg="serverStatus should include connections.active",
    ),
    DiagnosticTestCase(
        id="opcounters_insert_exists",
        checks={"opcounters.insert": Exists()},
        msg="serverStatus should include opcounters.insert",
    ),
    DiagnosticTestCase(
        id="opcounters_query_exists",
        checks={"opcounters.query": Exists()},
        msg="serverStatus should include opcounters.query",
    ),
    DiagnosticTestCase(
        id="opcounters_update_exists",
        checks={"opcounters.update": Exists()},
        msg="serverStatus should include opcounters.update",
    ),
    DiagnosticTestCase(
        id="opcounters_delete_exists",
        checks={"opcounters.delete": Exists()},
        msg="serverStatus should include opcounters.delete",
    ),
    DiagnosticTestCase(
        id="opcounters_getmore_exists",
        checks={"opcounters.getmore": Exists()},
        msg="serverStatus should include opcounters.getmore",
    ),
    DiagnosticTestCase(
        id="opcounters_command_exists",
        checks={"opcounters.command": Exists()},
        msg="serverStatus should include opcounters.command",
    ),
    DiagnosticTestCase(
        id="network_bytesIn_exists",
        checks={"network.bytesIn": Exists()},
        msg="serverStatus should include network.bytesIn",
    ),
    DiagnosticTestCase(
        id="network_bytesOut_exists",
        checks={"network.bytesOut": Exists()},
        msg="serverStatus should include network.bytesOut",
    ),
    DiagnosticTestCase(
        id="network_numRequests_exists",
        checks={"network.numRequests": Exists()},
        msg="serverStatus should include network.numRequests",
    ),
    DiagnosticTestCase(
        id="globalLock_totalTime_exists",
        checks={"globalLock.totalTime": Exists()},
        msg="serverStatus should include globalLock.totalTime",
    ),
    DiagnosticTestCase(
        id="globalLock_currentQueue_is_object",
        checks={"globalLock.currentQueue": IsType("object")},
        msg="serverStatus should return globalLock.currentQueue as an object",
    ),
    DiagnosticTestCase(
        id="globalLock_activeClients_is_object",
        checks={"globalLock.activeClients": IsType("object")},
        msg="serverStatus should return globalLock.activeClients as an object",
    ),
    DiagnosticTestCase(
        id="storageEngine_name_is_string",
        checks={"storageEngine.name": IsType("string")},
        msg="serverStatus should return storageEngine.name as a string",
    ),
    DiagnosticTestCase(
        id="storageEngine_name_is_nonempty",
        checks={"storageEngine.name": NonEmptyStr()},
        msg="serverStatus should return a non-empty storageEngine.name",
    ),
    DiagnosticTestCase(
        id="mem_resident_exists",
        checks={"mem.resident": Exists()},
        msg="serverStatus should include mem.resident",
    ),
    DiagnosticTestCase(
        id="mem_virtual_exists",
        checks={"mem.virtual": Exists()},
        msg="serverStatus should include mem.virtual",
    ),
    DiagnosticTestCase(
        id="catalogStats_collections_exists",
        checks={"catalogStats.collections": Exists()},
        msg="serverStatus should include catalogStats.collections",
    ),
    DiagnosticTestCase(
        id="catalogStats_capped_exists",
        checks={"catalogStats.capped": Exists()},
        msg="serverStatus should include catalogStats.capped",
    ),
    DiagnosticTestCase(
        id="catalogStats_views_exists",
        checks={"catalogStats.views": Exists()},
        msg="serverStatus should include catalogStats.views",
    ),
    DiagnosticTestCase(
        id="catalogStats_timeseries_exists",
        checks={"catalogStats.timeseries": Exists()},
        msg="serverStatus should include catalogStats.timeseries",
    ),
    DiagnosticTestCase(
        id="catalogStats_internalCollections_exists",
        checks={"catalogStats.internalCollections": Exists()},
        msg="serverStatus should include catalogStats.internalCollections",
    ),
    DiagnosticTestCase(
        id="catalogStats_internalViews_exists",
        checks={"catalogStats.internalViews": Exists()},
        msg="serverStatus should include catalogStats.internalViews",
    ),
]

RESPONSE_STRUCTURE_TESTS = TOP_LEVEL_TESTS + DEFAULT_SECTION_TESTS + SUB_DOC_TESTS


@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_serverStatus_response_structure(collection, test):
    """Verifies serverStatus response fields exist with expected types."""
    result = execute_admin_command(collection, {"serverStatus": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
