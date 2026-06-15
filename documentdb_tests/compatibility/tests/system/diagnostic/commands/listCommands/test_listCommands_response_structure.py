"""Tests for listCommands command response structure.

Validates the response format, field types, and presence of expected commands.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType

pytestmark = pytest.mark.admin


RESPONSE_FIELD_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="ok_is_1",
        checks={"ok": Eq(1.0)},
        msg="'ok' field should be 1.0",
    ),
    DiagnosticTestCase(
        id="commands_is_object",
        checks={"commands": IsType("object")},
        msg="'commands' field should be an object",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_FIELD_TESTS))
def test_listCommands_response_fields(collection, test):
    """Verify listCommands response contains expected fields with correct types."""
    result = execute_admin_command(collection, {"listCommands": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


COMMAND_ENTRY_STRUCTURE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="find_has_help",
        checks={"commands.find.help": IsType("string")},
        msg="Command entry 'find' should have 'help' field of type string",
    ),
    DiagnosticTestCase(
        id="find_has_adminOnly",
        checks={"commands.find.adminOnly": IsType("bool")},
        msg="Command entry 'find' should have 'adminOnly' field of type boolean",
    ),
    DiagnosticTestCase(
        id="find_has_requiresAuth",
        checks={"commands.find.requiresAuth": IsType("bool")},
        msg="Command entry 'find' should have 'requiresAuth' field of type boolean",
    ),
    DiagnosticTestCase(
        id="find_has_secondaryOk",
        checks={"commands.find.secondaryOk": IsType("bool")},
        msg="Command entry 'find' should have 'secondaryOk' field of type boolean",
    ),
    DiagnosticTestCase(
        id="find_has_apiVersions",
        checks={"commands.find.apiVersions": IsType("array")},
        msg="Command entry 'find' should have 'apiVersions' field of type array",
    ),
    DiagnosticTestCase(
        id="find_has_deprecatedApiVersions",
        checks={"commands.find.deprecatedApiVersions": IsType("array")},
        msg="Command entry 'find' should have 'deprecatedApiVersions' field of type array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMAND_ENTRY_STRUCTURE_TESTS))
def test_listCommands_command_entry_structure(collection, test):
    """Verify each command entry contains expected fields with correct types."""
    result = execute_admin_command(collection, {"listCommands": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


KNOWN_COMMANDS_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="find_present",
        checks={"commands.find": Exists()},
        msg="'find' should be listed",
    ),
    DiagnosticTestCase(
        id="insert_present",
        checks={"commands.insert": Exists()},
        msg="'insert' should be listed",
    ),
    DiagnosticTestCase(
        id="update_present",
        checks={"commands.update": Exists()},
        msg="'update' should be listed",
    ),
    DiagnosticTestCase(
        id="delete_present",
        checks={"commands.delete": Exists()},
        msg="'delete' should be listed",
    ),
    DiagnosticTestCase(
        id="aggregate_present",
        checks={"commands.aggregate": Exists()},
        msg="'aggregate' should be listed",
    ),
    DiagnosticTestCase(
        id="ping_present",
        checks={"commands.ping": Exists()},
        msg="'ping' should be listed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KNOWN_COMMANDS_TESTS))
def test_listCommands_known_commands_present(collection, test):
    """Verify well-known commands appear in the listCommands response."""
    result = execute_admin_command(collection, {"listCommands": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
