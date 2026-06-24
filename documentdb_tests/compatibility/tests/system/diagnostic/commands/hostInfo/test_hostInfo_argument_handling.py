"""Tests for hostInfo command argument handling.

hostInfo takes no arguments: the command value is ignored and any BSON type
is accepted, always returning ok:1.

Spec categories: rule_specs "Argument Validation" (accepted values/types),
test_tunable_rpo_js_specs "Basic command execution".
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


ARGUMENT_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "int_1", command={"hostInfo": 1}, checks={"ok": Eq(1.0)}, msg="Should accept int 1"
    ),
    DiagnosticTestCase(
        "int_0", command={"hostInfo": 0}, checks={"ok": Eq(1.0)}, msg="Should accept int 0"
    ),
    DiagnosticTestCase(
        "int_neg1", command={"hostInfo": -1}, checks={"ok": Eq(1.0)}, msg="Should accept int -1"
    ),
    DiagnosticTestCase(
        "bool_true", command={"hostInfo": True}, checks={"ok": Eq(1.0)}, msg="Should accept true"
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"hostInfo": False},
        checks={"ok": Eq(1.0)},
        msg="Should accept false",
    ),
    DiagnosticTestCase(
        "string",
        command={"hostInfo": "hello"},
        checks={"ok": Eq(1.0)},
        msg="Should accept string",
    ),
    DiagnosticTestCase(
        "null", command={"hostInfo": None}, checks={"ok": Eq(1.0)}, msg="Should accept null"
    ),
    DiagnosticTestCase(
        "empty_object",
        command={"hostInfo": {}},
        checks={"ok": Eq(1.0)},
        msg="Should accept empty object",
    ),
    DiagnosticTestCase(
        "empty_array",
        command={"hostInfo": []},
        checks={"ok": Eq(1.0)},
        msg="Should accept empty array",
    ),
    DiagnosticTestCase(
        "double", command={"hostInfo": 1.5}, checks={"ok": Eq(1.0)}, msg="Should accept double"
    ),
    DiagnosticTestCase(
        "int64", command={"hostInfo": Int64(1)}, checks={"ok": Eq(1.0)}, msg="Should accept int64"
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"hostInfo": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="Should accept decimal128",
    ),
    DiagnosticTestCase(
        "decimal128_nan",
        command={"hostInfo": Decimal128("NaN")},
        checks={"ok": Eq(1.0)},
        msg="Should accept decimal128 NaN",
    ),
    DiagnosticTestCase(
        "infinity",
        command={"hostInfo": float("inf")},
        checks={"ok": Eq(1.0)},
        msg="Should accept infinity",
    ),
    DiagnosticTestCase(
        "date",
        command={"hostInfo": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="Should accept date",
    ),
    DiagnosticTestCase(
        "binData",
        command={"hostInfo": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="Should accept binData",
    ),
    DiagnosticTestCase(
        "objectId",
        command={"hostInfo": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="Should accept objectId",
    ),
    DiagnosticTestCase(
        "regex",
        command={"hostInfo": Regex("test")},
        checks={"ok": Eq(1.0)},
        msg="Should accept regex",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"hostInfo": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="Should accept timestamp",
    ),
    DiagnosticTestCase(
        "minKey",
        command={"hostInfo": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="Should accept minKey",
    ),
    DiagnosticTestCase(
        "maxKey",
        command={"hostInfo": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="Should accept maxKey",
    ),
    DiagnosticTestCase(
        "code",
        command={"hostInfo": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="Should accept JavaScript code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TYPE_TESTS))
def test_hostInfo_argument_types(collection, test):
    """Test that hostInfo accepts various BSON types as argument value."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
