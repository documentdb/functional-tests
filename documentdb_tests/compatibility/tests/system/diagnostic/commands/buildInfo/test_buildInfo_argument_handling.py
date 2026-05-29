"""Tests for buildInfo command argument handling.

Validates that buildInfo accepts any BSON type as its argument value.
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
        "int_1", command={"buildInfo": 1}, checks={"ok": Eq(1.0)}, msg="Should accept int 1"
    ),
    DiagnosticTestCase(
        "int_0", command={"buildInfo": 0}, checks={"ok": Eq(1.0)}, msg="Should accept int 0"
    ),
    DiagnosticTestCase(
        "int_neg1", command={"buildInfo": -1}, checks={"ok": Eq(1.0)}, msg="Should accept int -1"
    ),
    DiagnosticTestCase(
        "bool_true", command={"buildInfo": True}, checks={"ok": Eq(1.0)}, msg="Should accept true"
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"buildInfo": False},
        checks={"ok": Eq(1.0)},
        msg="Should accept false",
    ),
    DiagnosticTestCase(
        "string", command={"buildInfo": "hello"}, checks={"ok": Eq(1.0)}, msg="Should accept string"
    ),
    DiagnosticTestCase(
        "null", command={"buildInfo": None}, checks={"ok": Eq(1.0)}, msg="Should accept null"
    ),
    DiagnosticTestCase(
        "empty_object",
        command={"buildInfo": {}},
        checks={"ok": Eq(1.0)},
        msg="Should accept empty object",
    ),
    DiagnosticTestCase(
        "empty_array",
        command={"buildInfo": []},
        checks={"ok": Eq(1.0)},
        msg="Should accept empty array",
    ),
    DiagnosticTestCase(
        "double", command={"buildInfo": 1.5}, checks={"ok": Eq(1.0)}, msg="Should accept double"
    ),
    DiagnosticTestCase(
        "int64", command={"buildInfo": Int64(1)}, checks={"ok": Eq(1.0)}, msg="Should accept int64"
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"buildInfo": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="Should accept decimal128",
    ),
    DiagnosticTestCase(
        "decimal128_nan",
        command={"buildInfo": Decimal128("NaN")},
        checks={"ok": Eq(1.0)},
        msg="Should accept decimal128 NaN",
    ),
    DiagnosticTestCase(
        "infinity",
        command={"buildInfo": float("inf")},
        checks={"ok": Eq(1.0)},
        msg="Should accept infinity",
    ),
    DiagnosticTestCase(
        "date",
        command={"buildInfo": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="Should accept date",
    ),
    DiagnosticTestCase(
        "binData",
        command={"buildInfo": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="Should accept binData",
    ),
    DiagnosticTestCase(
        "objectId",
        command={"buildInfo": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="Should accept objectId",
    ),
    DiagnosticTestCase(
        "regex",
        command={"buildInfo": Regex("test")},
        checks={"ok": Eq(1.0)},
        msg="Should accept regex",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"buildInfo": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="Should accept timestamp",
    ),
    DiagnosticTestCase(
        "minKey",
        command={"buildInfo": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="Should accept minKey",
    ),
    DiagnosticTestCase(
        "maxKey",
        command={"buildInfo": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="Should accept maxKey",
    ),
    DiagnosticTestCase(
        "code",
        command={"buildInfo": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="Should accept JavaScript code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TYPE_TESTS))
def test_buildInfo_argument_types(collection, test):
    """Test that buildInfo accepts various BSON types as argument value."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
