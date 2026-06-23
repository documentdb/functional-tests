"""Tests for getLog command response structure.

Covers response fields for the "global" filter (totalLinesWritten, log array
capped at 1024 entries with each entry truncated at 1024 characters, ok), the
"startupWarnings" filter (totalLinesWritten, log array, ok), and the "*"
filter (names array, ok). Each test asserts a single response property.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    ContainsElement,
    Eq,
    Gte,
    IsType,
    LenLte,
    StringsMaxLength,
)

pytestmark = pytest.mark.admin

MAX_LOG_EVENTS = 1024
MAX_LOG_LINE_CHARS = 1024


RESPONSE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "global_totalLinesWritten_number",
        command={"getLog": "global"},
        checks={"totalLinesWritten": Gte(0)},
        msg="global should return a non-negative totalLinesWritten",
    ),
    DiagnosticTestCase(
        "global_log_is_array",
        command={"getLog": "global"},
        checks={"log": IsType("array")},
        msg="global should return a log array",
    ),
    DiagnosticTestCase(
        "global_log_capped_at_1024",
        command={"getLog": "global"},
        checks={"log": LenLte(MAX_LOG_EVENTS)},
        msg="global log array should contain at most 1024 entries",
    ),
    DiagnosticTestCase(
        "global_log_entry_is_string",
        command={"getLog": "global"},
        checks={"log.0": IsType("string")},
        msg="global log entries should be JSON-formatted strings",
    ),
    DiagnosticTestCase(
        "global_log_entries_truncated_at_1024",
        command={"getLog": "global"},
        checks={"log": StringsMaxLength(MAX_LOG_LINE_CHARS)},
        msg="global log entries should be truncated to at most 1024 characters",
    ),
    DiagnosticTestCase(
        "global_ok",
        command={"getLog": "global"},
        checks={"ok": Eq(1.0)},
        msg="global should return ok:1",
    ),
    DiagnosticTestCase(
        "startupWarnings_log_is_array",
        command={"getLog": "startupWarnings"},
        checks={"log": IsType("array")},
        msg="startupWarnings should return a log array",
    ),
    DiagnosticTestCase(
        "startupWarnings_ok",
        command={"getLog": "startupWarnings"},
        checks={"ok": Eq(1.0)},
        msg="startupWarnings should return ok:1",
    ),
    DiagnosticTestCase(
        "startupWarnings_totalLinesWritten_number",
        command={"getLog": "startupWarnings"},
        checks={"totalLinesWritten": Gte(0)},
        msg="startupWarnings should return a non-negative totalLinesWritten",
    ),
    DiagnosticTestCase(
        "wildcard_names_is_array",
        command={"getLog": "*"},
        checks={"names": IsType("array")},
        msg="'*' should return a names array",
    ),
    DiagnosticTestCase(
        "wildcard_names_contains_global",
        command={"getLog": "*"},
        checks={"names": ContainsElement("global")},
        msg="'*' names should include 'global'",
    ),
    DiagnosticTestCase(
        "wildcard_names_contains_startupWarnings",
        command={"getLog": "*"},
        checks={"names": ContainsElement("startupWarnings")},
        msg="'*' names should include 'startupWarnings'",
    ),
    DiagnosticTestCase(
        "wildcard_ok",
        command={"getLog": "*"},
        checks={"ok": Eq(1.0)},
        msg="'*' should return ok:1",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_TESTS))
def test_getLog_response_properties(collection, test):
    """Verify a getLog response field exists and has the expected type or value."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
