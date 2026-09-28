"""Tests for serverStatus command argument handling.

Validates that serverStatus accepts any BSON type as its argument value.
The command field value is ignored by serverStatus.
"""

from __future__ import annotations

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


# Property [BSON Type Acceptance]: serverStatus accepts any BSON type as the command argument value.
ARGUMENT_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="int_1",
        command={"serverStatus": 1},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept int 1 as argument value",
    ),
    DiagnosticTestCase(
        id="int_0",
        command={"serverStatus": 0},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept int 0 as argument value",
    ),
    DiagnosticTestCase(
        id="int_neg1",
        command={"serverStatus": -1},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept negative int as argument value",
    ),
    DiagnosticTestCase(
        id="bool_true",
        command={"serverStatus": True},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept boolean true as argument value",
    ),
    DiagnosticTestCase(
        id="bool_false",
        command={"serverStatus": False},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept boolean false as argument value",
    ),
    DiagnosticTestCase(
        id="string",
        command={"serverStatus": "hello"},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept string as argument value",
    ),
    DiagnosticTestCase(
        id="empty_string",
        command={"serverStatus": ""},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept empty string as argument value",
    ),
    DiagnosticTestCase(
        id="null",
        command={"serverStatus": None},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept null as argument value",
    ),
    DiagnosticTestCase(
        id="empty_object",
        command={"serverStatus": {}},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept empty object as argument value",
    ),
    DiagnosticTestCase(
        id="empty_array",
        command={"serverStatus": []},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept empty array as argument value",
    ),
    DiagnosticTestCase(
        id="double",
        command={"serverStatus": 1.5},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept double as argument value",
    ),
    DiagnosticTestCase(
        id="int64",
        command={"serverStatus": Int64(1)},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept int64 as argument value",
    ),
    DiagnosticTestCase(
        id="decimal128",
        command={"serverStatus": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept Decimal128 as argument value",
    ),
    DiagnosticTestCase(
        id="decimal128_nan",
        command={"serverStatus": Decimal128("NaN")},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept Decimal128 NaN as argument value",
    ),
    DiagnosticTestCase(
        id="infinity",
        command={"serverStatus": float("inf")},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept infinity as argument value",
    ),
    DiagnosticTestCase(
        id="date",
        command={"serverStatus": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept datetime as argument value",
    ),
    DiagnosticTestCase(
        id="binData",
        command={"serverStatus": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept Binary as argument value",
    ),
    DiagnosticTestCase(
        id="objectId",
        command={"serverStatus": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept ObjectId as argument value",
    ),
    DiagnosticTestCase(
        id="regex",
        command={"serverStatus": Regex("test")},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept Regex as argument value",
    ),
    DiagnosticTestCase(
        id="timestamp",
        command={"serverStatus": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept Timestamp as argument value",
    ),
    DiagnosticTestCase(
        id="minKey",
        command={"serverStatus": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept MinKey as argument value",
    ),
    DiagnosticTestCase(
        id="maxKey",
        command={"serverStatus": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept MaxKey as argument value",
    ),
    DiagnosticTestCase(
        id="code",
        command={"serverStatus": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="serverStatus should accept JavaScript Code as argument value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TYPE_TESTS))
def test_serverStatus_argument_types(collection, test):
    """Test that serverStatus accepts various BSON types as argument value."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
