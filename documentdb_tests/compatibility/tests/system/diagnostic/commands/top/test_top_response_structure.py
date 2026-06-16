"""Tests for top command response structure.

Validates top-level response fields and per-collection event field structure.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte, IsType

pytestmark = pytest.mark.admin


# Property [Top-Level Fields]: top response contains totals and ok fields.
TOP_LEVEL_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="response_has_totals",
        checks={"totals": IsType("object")},
        msg="'totals' field should be an object",
    ),
    DiagnosticTestCase(
        id="response_has_ok",
        checks={"ok": Eq(1.0)},
        msg="'ok' field should be 1.0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TOP_LEVEL_TESTS))
def test_top_response_top_level(collection, test):
    """Test that top response contains expected top-level fields."""
    result = execute_admin_command(collection, {"top": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Per-Collection Event Fields]: each namespace entry has 9 event fields with time/count.
_EVENT_NAMES = [
    "total",
    "readLock",
    "writeLock",
    "queries",
    "getmore",
    "insert",
    "update",
    "remove",
    "commands",
]

EVENT_EXISTS_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id=f"event_{name}_exists",
        checks={name: IsType("object")},
        msg=f"'{name}' event field should be an object",
    )
    for name in _EVENT_NAMES
]

EVENT_TIME_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id=f"event_{name}_time_gte_0",
        checks={f"{name}.time": Gte(0)},
        msg=f"'{name}.time' should be >= 0",
    )
    for name in _EVENT_NAMES
]

EVENT_COUNT_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id=f"event_{name}_count_gte_0",
        checks={f"{name}.count": Gte(0)},
        msg=f"'{name}.count' should be >= 0",
    )
    for name in _EVENT_NAMES
]

EVENT_FIELD_TESTS = EVENT_EXISTS_TESTS + EVENT_TIME_TESTS + EVENT_COUNT_TESTS


@pytest.mark.parametrize("test", pytest_params(EVENT_FIELD_TESTS))
def test_top_event_field_structure(collection, test):
    """Test that per-collection event fields have expected structure."""
    collection.insert_one({"_id": "event_structure_probe"})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"][ns]
    assertProperties(ns_data, test.checks, msg=test.msg, raw_res=True)
