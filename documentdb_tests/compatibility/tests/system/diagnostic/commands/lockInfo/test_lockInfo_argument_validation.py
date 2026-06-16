"""Tests for lockInfo command argument validation.

Verifies that lockInfo accepts various values for the command field and
rejects unrecognized fields with error code 40415.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


ARG_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "int_1", command={"lockInfo": 1}, checks={"ok": Eq(1.0)}, msg="int 1 should succeed"
    ),
    DiagnosticTestCase(
        "int_0", command={"lockInfo": 0}, checks={"ok": Eq(1.0)}, msg="int 0 should succeed"
    ),
    DiagnosticTestCase(
        "double", command={"lockInfo": 1.5}, checks={"ok": Eq(1.0)}, msg="double should succeed"
    ),
    DiagnosticTestCase(
        "long", command={"lockInfo": Int64(1)}, checks={"ok": Eq(1.0)}, msg="long should succeed"
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"lockInfo": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="decimal128 should succeed",
    ),
    DiagnosticTestCase(
        "string",
        command={"lockInfo": "test"},
        checks={"ok": Eq(1.0)},
        msg="string should succeed",
    ),
    DiagnosticTestCase(
        "bool_true",
        command={"lockInfo": True},
        checks={"ok": Eq(1.0)},
        msg="bool true should succeed",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"lockInfo": False},
        checks={"ok": Eq(1.0)},
        msg="bool false should succeed",
    ),
    DiagnosticTestCase(
        "date",
        command={"lockInfo": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="date should succeed",
    ),
    DiagnosticTestCase(
        "null", command={"lockInfo": None}, checks={"ok": Eq(1.0)}, msg="null should succeed"
    ),
    DiagnosticTestCase(
        "object", command={"lockInfo": {}}, checks={"ok": Eq(1.0)}, msg="object should succeed"
    ),
    DiagnosticTestCase(
        "array", command={"lockInfo": []}, checks={"ok": Eq(1.0)}, msg="array should succeed"
    ),
    DiagnosticTestCase(
        "binData",
        command={"lockInfo": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="binData should succeed",
    ),
    DiagnosticTestCase(
        "objectId",
        command={"lockInfo": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="objectId should succeed",
    ),
    DiagnosticTestCase(
        "regex",
        command={"lockInfo": Regex("test")},
        checks={"ok": Eq(1.0)},
        msg="regex should succeed",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"lockInfo": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="timestamp should succeed",
    ),
    DiagnosticTestCase(
        "minKey",
        command={"lockInfo": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="minKey should succeed",
    ),
    DiagnosticTestCase(
        "maxKey",
        command={"lockInfo": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="maxKey should succeed",
    ),
    DiagnosticTestCase(
        "code",
        command={"lockInfo": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="code should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARG_TYPE_TESTS))
def test_lockInfo_accepts_any_type(collection, test):
    """Verify lockInfo succeeds when the command field value is a given BSON type."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_lockInfo_unrecognized_field(collection):
    """Test lockInfo with unrecognized extra field returns error 40415."""
    result = execute_admin_command(collection, {"lockInfo": 1, "foo": 1})
    assertFailureCode(
        result, UNRECOGNIZED_COMMAND_FIELD_ERROR, msg="Unrecognized field should error"
    )
