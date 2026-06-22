"""Tests for getLog "global" log content behavior.

Covers the stable, deterministic parts of getLog's logging contract: a running
server returns log entries from its RAM cache, totalLinesWritten is consistent
with the returned log array, the array is capped at 1024 entries, entries are
JSON-parseable strings, and totalLinesWritten does not decrease across a
logRotate.

Non-deterministic behaviors documented for getLog — exact >1024-character line
truncation, specific character-escape sequences, and which particular messages
appear after a logRotate — depend on runtime log content and are intentionally
not asserted here.
"""

import json

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, Gte

pytestmark = pytest.mark.admin

# getLog "global" returns at most the most recent 1024 logged events.
MAX_LOG_EVENTS = 1024


def _parses_as_json(entry: object) -> bool:
    """Return True if entry is a string that parses as a JSON document."""
    if not isinstance(entry, str):
        return False
    try:
        json.loads(entry)
        return True
    except ValueError:
        return False


PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "has_log_entries",
        command={"getLog": "global"},
        checks={"log.0": Exists()},
        msg="A running server should have log entries",
    ),
    DiagnosticTestCase(
        "totalLinesWritten_non_zero",
        command={"getLog": "global"},
        checks={"totalLinesWritten": Gte(1)},
        msg="totalLinesWritten should be >= 1 on a running server",
    ),
]

BEHAVIOR_CASES = [
    pytest.param(
        "totalLinesWritten should be >= len(log)",
        lambda r: r["totalLinesWritten"] >= len(r["log"]),
        id="totalLinesWritten_gte_log_length",
    ),
    pytest.param(
        "log array should contain at most 1024 entries",
        lambda r: len(r["log"]) <= MAX_LOG_EVENTS,
        id="log_capped_at_1024",
    ),
    pytest.param(
        "log entries should be JSON-parseable strings",
        lambda r: all(_parses_as_json(entry) for entry in r["log"]),
        id="entries_parse_as_json",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_getLog_global_properties(collection, test):
    """Verify a getLog 'global' response field exists and has the expected type or value."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


@pytest.mark.parametrize("msg,transform", BEHAVIOR_CASES)
def test_getLog_global_invariants(collection, msg, transform):
    """Verify stable invariants of the getLog 'global' log array and line counter."""
    result = execute_admin_command(collection, {"getLog": "global"})
    assertSuccess(result, True, msg=msg, raw_res=True, transform=transform)


def test_getLog_totalLinesWritten_non_decreasing_after_logRotate(collection):
    """Test totalLinesWritten does not decrease across a logRotate."""
    before = execute_admin_command(collection, {"getLog": "global"})
    before_count = before["totalLinesWritten"]
    execute_admin_command(collection, {"logRotate": 1})
    after = execute_admin_command(collection, {"getLog": "global"})
    assertSuccess(
        after,
        True,
        msg="totalLinesWritten should not decrease after logRotate",
        raw_res=True,
        transform=lambda r: r["totalLinesWritten"] >= before_count,
    )
