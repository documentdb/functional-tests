"""Tests for serverStatus command field toggle behavior.

Validates section inclusion/exclusion via field toggles, multiple
toggle combinations, and toggle value coercion.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists

pytestmark = pytest.mark.admin


# Property [Section Exclusion]: serverStatus omits a section when its toggle is set to 0.
EXCLUDE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="exclude_metrics",
        command={"serverStatus": 1, "metrics": 0},
        checks={"metrics": NotExists()},
        msg="serverStatus should exclude metrics when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_locks",
        command={"serverStatus": 1, "locks": 0},
        checks={"locks": NotExists()},
        msg="serverStatus should exclude locks when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_connections",
        command={"serverStatus": 1, "connections": 0},
        checks={"connections": NotExists()},
        msg="serverStatus should exclude connections when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_opcounters",
        command={"serverStatus": 1, "opcounters": 0},
        checks={"opcounters": NotExists()},
        msg="serverStatus should exclude opcounters when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_asserts",
        command={"serverStatus": 1, "asserts": 0},
        checks={"asserts": NotExists()},
        msg="serverStatus should exclude asserts when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_network",
        command={"serverStatus": 1, "network": 0},
        checks={"network": NotExists()},
        msg="serverStatus should exclude network when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_globalLock",
        command={"serverStatus": 1, "globalLock": 0},
        checks={"globalLock": NotExists()},
        msg="serverStatus should exclude globalLock when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_extra_info",
        command={"serverStatus": 1, "extra_info": 0},
        checks={"extra_info": NotExists()},
        msg="serverStatus should exclude extra_info when set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_transactions",
        command={"serverStatus": 1, "transactions": 0},
        checks={"transactions": NotExists()},
        msg="serverStatus should exclude transactions when set to 0",
    ),
]

# Property [Section Inclusion]: serverStatus includes non-default sections when toggled to 1.
INCLUDE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="include_mirroredReads",
        command={"serverStatus": 1, "mirroredReads": 1},
        checks={"mirroredReads": Exists()},
        msg="serverStatus should include mirroredReads when set to 1",
    ),
]

# Property [Multiple Toggles]: serverStatus respects multiple section toggles simultaneously.
MULTIPLE_TOGGLE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="exclude_multiple_sections",
        command={"serverStatus": 1, "metrics": 0, "locks": 0, "asserts": 0},
        checks={
            "metrics": NotExists(),
            "locks": NotExists(),
            "asserts": NotExists(),
            "connections": IsType("object"),
            "opcounters": IsType("object"),
        },
        msg="serverStatus should exclude multiple sections when each is set to 0",
    ),
    DiagnosticTestCase(
        id="exclude_some_include_some",
        command={"serverStatus": 1, "metrics": 0, "mirroredReads": 1},
        checks={
            "metrics": NotExists(),
            "mirroredReads": Exists(),
        },
        msg="serverStatus should respect mixed include and exclude toggles",
    ),
]

# Property [Toggle Value Coercion]: serverStatus coerces toggle values to truthy or falsy.
TOGGLE_COERCION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="toggle_false_excludes",
        command={"serverStatus": 1, "metrics": False},
        checks={"metrics": NotExists()},
        msg="serverStatus should exclude section when toggle is boolean false",
    ),
    DiagnosticTestCase(
        id="toggle_true_includes",
        command={"serverStatus": 1, "mirroredReads": True},
        checks={"mirroredReads": Exists()},
        msg="serverStatus should include section when toggle is boolean true",
    ),
    DiagnosticTestCase(
        id="toggle_negative_includes",
        command={"serverStatus": 1, "mirroredReads": -1},
        checks={"mirroredReads": Exists()},
        msg="serverStatus should include section when toggle is negative int (truthy)",
    ),
    DiagnosticTestCase(
        id="toggle_string_includes",
        command={"serverStatus": 1, "mirroredReads": "hello"},
        checks={"mirroredReads": Exists()},
        msg="serverStatus should include section when toggle is string (truthy)",
    ),
    DiagnosticTestCase(
        id="toggle_null_excludes",
        command={"serverStatus": 1, "metrics": None},
        checks={"metrics": NotExists()},
        msg="serverStatus should exclude section when toggle is null (falsy)",
    ),
    DiagnosticTestCase(
        id="toggle_object_includes",
        command={"serverStatus": 1, "mirroredReads": {}},
        checks={"mirroredReads": Exists()},
        msg="serverStatus should include section when toggle is empty object (truthy)",
    ),
    DiagnosticTestCase(
        id="toggle_array_includes",
        command={"serverStatus": 1, "mirroredReads": []},
        checks={"mirroredReads": Exists()},
        msg="serverStatus should include section when toggle is empty array (truthy)",
    ),
]

# Property [Core Fields Preserved]: serverStatus core fields are unaffected by section toggles.
CORE_FIELDS_PRESERVED_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="core_fields_present_with_exclusions",
        command={"serverStatus": 1, "metrics": 0, "locks": 0},
        checks={
            "ok": Exists(),
            "host": Exists(),
            "version": Exists(),
            "process": Exists(),
            "pid": Exists(),
            "uptime": Exists(),
            "localTime": Exists(),
        },
        msg="serverStatus should include core fields even when optional sections are excluded",
    ),
]

# Property [Default Exclusions]: serverStatus omits certain sections by default.
DEFAULT_EXCLUSION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="mirroredReads_excluded_by_default",
        command={"serverStatus": 1},
        checks={"mirroredReads": NotExists()},
        msg="serverStatus should exclude mirroredReads by default",
    ),
]

# Property [Unrecognized Fields]: serverStatus accepts unknown fields as section toggles.
UNRECOGNIZED_FIELD_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="unrecognized_field_accepted",
        command={"serverStatus": 1, "completelyFakeFieldName": 1},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept unrecognized fields as section toggles",
    ),
]

TOGGLE_TESTS = (
    EXCLUDE_TESTS
    + INCLUDE_TESTS
    + MULTIPLE_TOGGLE_TESTS
    + TOGGLE_COERCION_TESTS
    + CORE_FIELDS_PRESERVED_TESTS
    + DEFAULT_EXCLUSION_TESTS
    + UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TOGGLE_TESTS))
def test_serverStatus_field_toggle(collection, test):
    """Verifies serverStatus section toggle behavior."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
