"""Tests for connPoolStats command response structure."""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticPropertyTest,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Gte, IsType

pytestmark = pytest.mark.admin


RESPONSE_PROPERTY_TESTS: list[DiagnosticPropertyTest] = [
    DiagnosticPropertyTest(
        id="totalInUse_gte_0",
        checks={"totalInUse": Gte(0)},
        msg="totalInUse should be >= 0",
    ),
    DiagnosticPropertyTest(
        id="totalAvailable_gte_0",
        checks={"totalAvailable": Gte(0)},
        msg="totalAvailable should be >= 0",
    ),
    DiagnosticPropertyTest(
        id="totalCreated_gte_0",
        checks={"totalCreated": Gte(0)},
        msg="totalCreated should be >= 0",
    ),
    DiagnosticPropertyTest(
        id="totalRefreshing_gte_0",
        checks={"totalRefreshing": Gte(0)},
        msg="totalRefreshing should be >= 0",
    ),
    DiagnosticPropertyTest(
        id="pools_is_object",
        checks={"pools": IsType("object")},
        msg="pools should be a document",
    ),
    DiagnosticPropertyTest(
        id="hosts_is_object",
        checks={"hosts": IsType("object")},
        msg="hosts should be a document",
    ),
    DiagnosticPropertyTest(
        id="numClientConnections_gte_0",
        checks={"numClientConnections": Gte(0)},
        msg="numClientConnections should be >= 0",
    ),
    DiagnosticPropertyTest(
        id="numAScopedConnections_gte_0",
        checks={"numAScopedConnections": Gte(0)},
        msg="numAScopedConnections should be >= 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_PROPERTY_TESTS))
def test_connPoolStats_response_properties(collection, test):
    """Verify a connPoolStats response field exists and has the expected type or value."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
