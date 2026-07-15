"""Tests for profile command filter parameter.

Validates filter object acceptance, the special "unset" string, filter
normalization, and the set/unset lifecycle. All tests in this file verify
success cases only.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, NotExists

pytestmark = [pytest.mark.no_parallel]

# Property [Filter Object Acceptance]: the filter field accepts object values
# and the filter is actually applied.
FILTER_ACCEPT_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "empty_object",
        setup=[{"profile": 1, "filter": {}}],
        command={"profile": -1},
        checks={"filter": Exists()},
        msg="filter should accept an empty object and be visible",
    ),
    DiagnosticTestCase(
        "op_query",
        setup=[{"profile": 1, "filter": {"op": "query"}}],
        command={"profile": -1},
        checks={"filter": Exists()},
        msg="filter should accept {op: 'query'} and be visible",
    ),
    DiagnosticTestCase(
        "op_in",
        setup=[{"profile": 1, "filter": {"op": {"$in": ["query", "command"]}}}],
        command={"profile": -1},
        checks={"filter": Exists()},
        msg="filter should accept $in expression and be visible",
    ),
    DiagnosticTestCase(
        "ns_filter",
        setup=[{"profile": 1, "filter": {"ns": "test.users"}}],
        command={"profile": -1},
        checks={"filter": Exists()},
        msg="filter should accept namespace filter and be visible",
    ),
    DiagnosticTestCase(
        "unset_removes_filter",
        setup=[
            {"profile": 1, "filter": {"op": "query"}},
            {"profile": 1, "filter": "unset"},
        ],
        command={"profile": -1},
        checks={"filter": NotExists()},
        msg="filter should accept 'unset' and remove the filter",
    ),
]


# Property [Filter Normalization]: simple equality in the filter is normalized
# to $eq form in the response.
FILTER_NORMALIZATION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "normalize_eq",
        setup=[{"profile": 1, "filter": {"op": "query"}}],
        command={"profile": -1},
        checks={"filter": Eq({"op": {"$eq": "query"}})},
        msg="filter should normalize {op: 'query'} to {op: {$eq: 'query'}}",
    ),
]

FILTER_TESTS = FILTER_ACCEPT_TESTS + FILTER_NORMALIZATION_TESTS


@pytest.mark.parametrize("test", pytest_params(FILTER_TESTS))
def test_profile_filter(collection, test):
    """Test profile filter parameter behavior."""
    for cmd in test.setup:
        execute_command(collection, cmd)
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
    execute_command(collection, {"profile": 0, "filter": "unset"})
