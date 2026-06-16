"""Tests for lockInfo command response structure.

Verifies the structure of the lockInfo response including field types
and lock mode values in granted/pending entries.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType

pytestmark = pytest.mark.admin


RESPONSE_STRUCTURE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "ok_field",
        checks={"ok": Eq(1.0)},
        msg="Response should contain ok: 1.0",
    ),
    DiagnosticTestCase(
        "lockInfo_is_array",
        checks={"lockInfo": IsType("array")},
        msg="lockInfo field should be an array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_lockInfo_response_structure(collection, test):
    """Verify lockInfo response contains expected fields with correct types."""
    result = execute_admin_command(collection, {"lockInfo": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_lockInfo_entry_resourceId_is_string(collection):
    """Test lock entry contains resourceId field as a string."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"lockInfo": 1})
    entry = result.get("lockInfo", [{}])[0] if result.get("lockInfo") else {}
    assertProperties(
        {"resourceId": entry.get("resourceId", "")},
        {"resourceId": IsType("string")},
        msg="resourceId should be a string",
        raw_res=True,
    )


def test_lockInfo_entry_granted_is_array(collection):
    """Test lock entry contains granted field as an array."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"lockInfo": 1})
    entry = result.get("lockInfo", [{}])[0] if result.get("lockInfo") else {}
    assertProperties(
        {"granted": entry.get("granted", [])},
        {"granted": IsType("array")},
        msg="granted should be an array",
        raw_res=True,
    )


def test_lockInfo_entry_pending_is_array(collection):
    """Test lock entry contains pending field as an array."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"lockInfo": 1})
    entry = result.get("lockInfo", [{}])[0] if result.get("lockInfo") else {}
    assertProperties(
        {"pending": entry.get("pending", [])},
        {"pending": IsType("array")},
        msg="pending should be an array",
        raw_res=True,
    )
