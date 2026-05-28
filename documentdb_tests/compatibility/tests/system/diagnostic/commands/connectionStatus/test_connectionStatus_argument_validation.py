"""Tests for connectionStatus command argument validation.

Verifies that connectionStatus accepts all BSON types as the command field
value and returns ok: 1 for each.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


ARG_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "int_1", command={"connectionStatus": 1}, checks={"ok": Eq(1.0)}, msg="int should succeed"
    ),
    DiagnosticTestCase(
        "int_0",
        command={"connectionStatus": 0},
        checks={"ok": Eq(1.0)},
        msg="int 0 should succeed",
    ),
    DiagnosticTestCase(
        "double",
        command={"connectionStatus": 1.5},
        checks={"ok": Eq(1.0)},
        msg="double should succeed",
    ),
    DiagnosticTestCase(
        "long",
        command={"connectionStatus": Int64(1)},
        checks={"ok": Eq(1.0)},
        msg="long should succeed",
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"connectionStatus": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="decimal128 should succeed",
    ),
    DiagnosticTestCase(
        "string",
        command={"connectionStatus": "test"},
        checks={"ok": Eq(1.0)},
        msg="string should succeed",
    ),
    DiagnosticTestCase(
        "bool_true",
        command={"connectionStatus": True},
        checks={"ok": Eq(1.0)},
        msg="bool true should succeed",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"connectionStatus": False},
        checks={"ok": Eq(1.0)},
        msg="bool false should succeed",
    ),
    DiagnosticTestCase(
        "date",
        command={"connectionStatus": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="date should succeed",
    ),
    DiagnosticTestCase(
        "null",
        command={"connectionStatus": None},
        checks={"ok": Eq(1.0)},
        msg="null should succeed",
    ),
    DiagnosticTestCase(
        "object",
        command={"connectionStatus": {}},
        checks={"ok": Eq(1.0)},
        msg="object should succeed",
    ),
    DiagnosticTestCase(
        "array",
        command={"connectionStatus": []},
        checks={"ok": Eq(1.0)},
        msg="array should succeed",
    ),
    DiagnosticTestCase(
        "binData",
        command={"connectionStatus": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="binData should succeed",
    ),
    DiagnosticTestCase(
        "objectId",
        command={"connectionStatus": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="objectId should succeed",
    ),
    DiagnosticTestCase(
        "regex",
        command={"connectionStatus": Regex("test")},
        checks={"ok": Eq(1.0)},
        msg="regex should succeed",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"connectionStatus": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="timestamp should succeed",
    ),
    DiagnosticTestCase(
        "minKey",
        command={"connectionStatus": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="minKey should succeed",
    ),
    DiagnosticTestCase(
        "maxKey",
        command={"connectionStatus": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="maxKey should succeed",
    ),
    DiagnosticTestCase(
        "code",
        command={"connectionStatus": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="code should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARG_TYPE_TESTS))
def test_connectionStatus_accepts_any_type(collection, test):
    """Verify connectionStatus succeeds when the command field value is a given BSON type."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
