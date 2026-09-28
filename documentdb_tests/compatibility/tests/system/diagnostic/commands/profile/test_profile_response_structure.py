"""Tests for profile command response structure.

Validates presence, types, and values of response fields returned by the
profile command, including base fields and filter-related fields.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists

pytestmark = [pytest.mark.no_parallel]

# Property [Base Response Fields]: every successful profile command response
# includes was (int), slowms (int), sampleRate (double), and ok (1.0).
RESPONSE_BASE_FIELD_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "base_fields_at_level_neg1",
        command={"profile": -1},
        checks={
            "was": IsType("int"),
            "slowms": IsType("int"),
            "sampleRate": IsType("double"),
            "ok": Eq(1.0),
        },
        msg="profile -1 response should include was, slowms, sampleRate, and ok",
    ),
    DiagnosticTestCase(
        "base_fields_at_level_0",
        command={"profile": 0},
        checks={
            "was": IsType("int"),
            "slowms": IsType("int"),
            "sampleRate": IsType("double"),
            "ok": Eq(1.0),
        },
        msg="profile 0 response should include was, slowms, sampleRate, and ok",
    ),
]

# Property [Filter Response Fields]: when a filter is active the response
# includes filter and note; after unset they are absent.
RESPONSE_FILTER_FIELD_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "filter_fields_present",
        setup=[{"profile": 1, "filter": {"op": "query"}}],
        command={"profile": -1},
        checks={"filter": Exists(), "note": IsType("string")},
        msg="profile response should include filter and note when a filter is active",
    ),
    DiagnosticTestCase(
        "filter_fields_absent_after_unset",
        setup=[
            {"profile": 1, "filter": {"op": "query"}},
            {"profile": 1, "filter": "unset"},
        ],
        command={"profile": -1},
        checks={"filter": NotExists(), "note": NotExists()},
        msg="profile response should exclude filter and note after filter is unset",
    ),
]

RESPONSE_STRUCTURE_TESTS = RESPONSE_BASE_FIELD_TESTS + RESPONSE_FILTER_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_profile_response_structure(collection, test):
    """Test profile response field presence and types."""
    for cmd in test.setup:
        execute_command(collection, cmd)
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
    execute_command(collection, {"profile": 0, "filter": "unset"})
