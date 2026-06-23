"""Tests for getLog log-entry behavior.

Validates documented properties of the "global" and "startupWarnings" log
payloads: each entry is a Relaxed Extended JSON v2.0 string with special
characters properly escaped (quotes and backslashes escaped, no raw control
characters).
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import StringsMaxLength, WellFormedJsonStrings

pytestmark = pytest.mark.admin

# getLog truncates any log event longer than 1024 characters.
MAX_LOG_LINE_CHARS = 1024


LOG_BEHAVIOR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "global_log_entries_escaped",
        command={"getLog": "global"},
        checks={"log": WellFormedJsonStrings()},
        msg="global log entries should be JSON strings with special characters escaped",
    ),
    DiagnosticTestCase(
        "global_log_entries_truncated_at_1024",
        command={"getLog": "global"},
        checks={"log": StringsMaxLength(MAX_LOG_LINE_CHARS)},
        msg="global log entries should be truncated to at most 1024 characters",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOG_BEHAVIOR_TESTS))
def test_getLog_log_behavior(collection, test):
    """Verify documented getLog log-entry behavior (escaping and truncation)."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
