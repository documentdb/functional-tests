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

from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_admin_command
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


def test_getLog_global_has_log_entries(collection):
    """Test getLog 'global' returns at least one log entry from the RAM cache."""
    result = execute_admin_command(collection, {"getLog": "global"})
    assertProperties(
        result, {"log.0": Exists()}, msg="A running server should have log entries", raw_res=True
    )


def test_getLog_global_totalLinesWritten_non_zero(collection):
    """Test getLog 'global' reports a non-zero totalLinesWritten on a running server."""
    result = execute_admin_command(collection, {"getLog": "global"})
    assertProperties(
        result,
        {"totalLinesWritten": Gte(1)},
        msg="totalLinesWritten should be >= 1 on a running server",
        raw_res=True,
    )


def test_getLog_global_totalLinesWritten_gte_log_length(collection):
    """Test totalLinesWritten is >= the number of returned log entries."""
    result = execute_admin_command(collection, {"getLog": "global"})
    assertSuccess(
        result,
        True,
        msg="totalLinesWritten should be >= len(log)",
        raw_res=True,
        transform=lambda r: r["totalLinesWritten"] >= len(r["log"]),
    )


def test_getLog_global_log_capped_at_1024(collection):
    """Test getLog 'global' returns at most 1024 log entries."""
    result = execute_admin_command(collection, {"getLog": "global"})
    assertSuccess(
        result,
        True,
        msg="log array should contain at most 1024 entries",
        raw_res=True,
        transform=lambda r: len(r["log"]) <= MAX_LOG_EVENTS,
    )


def test_getLog_global_entries_parse_as_json(collection):
    """Test every getLog 'global' log entry is a JSON-parseable string."""
    result = execute_admin_command(collection, {"getLog": "global"})
    assertSuccess(
        result,
        True,
        msg="log entries should be JSON-parseable strings",
        raw_res=True,
        transform=lambda r: all(_parses_as_json(entry) for entry in r["log"]),
    )


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
