"""Tests for whatsmyuri command argument handling.

Validates that whatsmyuri accepts any BSON type as its argument value
and ignores unrecognized fields.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


# Property [Type Acceptance]: whatsmyuri accepts all BSON types as the command field value.
ARGUMENT_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "int_1",
        command={"whatsmyuri": 1},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept int 1",
    ),
    DiagnosticTestCase(
        "int_0",
        command={"whatsmyuri": 0},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept int 0",
    ),
    DiagnosticTestCase(
        "int_neg1",
        command={"whatsmyuri": -1},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept int -1",
    ),
    DiagnosticTestCase(
        "bool_true",
        command={"whatsmyuri": True},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept true",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"whatsmyuri": False},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept false",
    ),
    DiagnosticTestCase(
        "string",
        command={"whatsmyuri": "hello"},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept string",
    ),
    DiagnosticTestCase(
        "empty_string",
        command={"whatsmyuri": ""},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept empty string",
    ),
    DiagnosticTestCase(
        "null",
        command={"whatsmyuri": None},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept null",
    ),
    DiagnosticTestCase(
        "empty_object",
        command={"whatsmyuri": {}},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept empty object",
    ),
    DiagnosticTestCase(
        "nested_object",
        command={"whatsmyuri": {"a": {"b": 1}}},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept nested object",
    ),
    DiagnosticTestCase(
        "empty_array",
        command={"whatsmyuri": []},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept empty array",
    ),
    DiagnosticTestCase(
        "array_with_elements",
        command={"whatsmyuri": [1, 2, 3]},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept array with elements",
    ),
    DiagnosticTestCase(
        "double",
        command={"whatsmyuri": 1.5},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept double",
    ),
    DiagnosticTestCase(
        "negative_double",
        command={"whatsmyuri": -1.5},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept negative double",
    ),
    DiagnosticTestCase(
        "large_int",
        command={"whatsmyuri": 999_999_999},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept large int",
    ),
    DiagnosticTestCase(
        "int64",
        command={"whatsmyuri": Int64(1)},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept int64",
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"whatsmyuri": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept decimal128",
    ),
    DiagnosticTestCase(
        "decimal128_nan",
        command={"whatsmyuri": Decimal128("NaN")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept decimal128 NaN",
    ),
    DiagnosticTestCase(
        "decimal128_infinity",
        command={"whatsmyuri": Decimal128("Infinity")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept decimal128 Infinity",
    ),
    DiagnosticTestCase(
        "decimal128_neg_zero",
        command={"whatsmyuri": Decimal128("-0")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept decimal128 negative zero",
    ),
    DiagnosticTestCase(
        "infinity",
        command={"whatsmyuri": float("inf")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept infinity",
    ),
    DiagnosticTestCase(
        "neg_infinity",
        command={"whatsmyuri": float("-inf")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept negative infinity",
    ),
    DiagnosticTestCase(
        "nan",
        command={"whatsmyuri": float("nan")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept NaN",
    ),
    DiagnosticTestCase(
        "date",
        command={"whatsmyuri": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept date",
    ),
    DiagnosticTestCase(
        "binData",
        command={"whatsmyuri": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept binData",
    ),
    DiagnosticTestCase(
        "objectId",
        command={"whatsmyuri": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept objectId",
    ),
    DiagnosticTestCase(
        "regex",
        command={"whatsmyuri": Regex("test")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept regex",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"whatsmyuri": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept timestamp",
    ),
    DiagnosticTestCase(
        "minKey",
        command={"whatsmyuri": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept minKey",
    ),
    DiagnosticTestCase(
        "maxKey",
        command={"whatsmyuri": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept maxKey",
    ),
    DiagnosticTestCase(
        "code",
        command={"whatsmyuri": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should accept JavaScript code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TYPE_TESTS))
def test_whatsmyuri_argument_types(collection, test):
    """Test whatsmyuri argument type acceptance."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Extra Fields Ignored]: whatsmyuri ignores unrecognized fields.
def test_whatsmyuri_extra_field_ignored(collection):
    """Test whatsmyuri succeeds with unrecognized fields."""
    result = execute_admin_command(collection, {"whatsmyuri": 1, "unknownField": 1})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="whatsmyuri should succeed even with unrecognized fields",
    )
