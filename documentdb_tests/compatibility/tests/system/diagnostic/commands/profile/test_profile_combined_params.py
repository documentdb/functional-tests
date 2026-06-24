"""Tests for profile command with multiple parameters and cross-database behavior.

Validates setting multiple parameters simultaneously and cross-database
behavior. All tests in this file verify success cases only.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType

pytestmark = [pytest.mark.no_parallel]

# Property [Multi-Parameter Set]: setting level, slowms, sampleRate, and
# filter simultaneously applies all values.
MULTI_PARAM_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "level_slowms_samplerate",
        setup=[{"profile": 1, "slowms": 50, "sampleRate": 0.5}],
        command={"profile": -1},
        use_admin=False,
        checks={"was": Eq(1), "slowms": Eq(50), "sampleRate": Eq(0.5)},
        msg="profile should apply level, slowms, and sampleRate together",
    ),
    DiagnosticTestCase(
        "level_slowms_filter",
        setup=[{"profile": 1, "slowms": 50, "filter": {"op": "query"}}],
        command={"profile": -1},
        use_admin=False,
        checks={"was": Eq(1), "slowms": Eq(50), "filter": Exists()},
        msg="profile should apply level, slowms, and filter together",
    ),
    DiagnosticTestCase(
        "params_persist_when_profiling_disabled",
        setup=[{"profile": 0, "slowms": 200, "sampleRate": 0.8}],
        command={"profile": -1},
        use_admin=False,
        checks={"was": Eq(0), "slowms": Eq(200), "sampleRate": Eq(0.8)},
        msg="profile should apply slowms and sampleRate even when profiler is off",
    ),
]

# Property [Database Scope]: profile operates on both regular and admin
# databases and returns the full response structure.
DATABASE_SCOPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "regular_database",
        command={"profile": -1},
        use_admin=False,
        checks={
            "was": IsType("int"),
            "slowms": IsType("int"),
            "sampleRate": IsType("double"),
            "ok": Eq(1.0),
        },
        msg="profile should return full response on a regular database",
    ),
    DiagnosticTestCase(
        "admin_database",
        command={"profile": -1},
        use_admin=True,
        checks={
            "was": IsType("int"),
            "slowms": IsType("int"),
            "sampleRate": IsType("double"),
            "ok": Eq(1.0),
        },
        msg="profile should return full response on the admin database",
    ),
]

COMBINED_TESTS = MULTI_PARAM_TESTS + DATABASE_SCOPE_TESTS


@pytest.mark.parametrize("test", pytest_params(COMBINED_TESTS))
def test_profile_combined_params(collection, test):
    """Test profile command with multiple parameters and database scope."""
    for cmd in test.setup:
        execute_command(collection, cmd)
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
    execute_command(collection, {"profile": 0, "sampleRate": 1.0, "filter": "unset"})
