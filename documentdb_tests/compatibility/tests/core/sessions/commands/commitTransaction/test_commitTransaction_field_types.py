"""Tests for commitTransaction command field type acceptance in a real transaction.

Validates that the commitTransaction command's primary field accepts all BSON
types when issued inside an active transaction on a replica set.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_test_case import (
    SessionOp,
    SessionOperation,
    SessionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_session_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]

# Property [Field Type Acceptance]: the command field accepts any BSON type.
FIELD_TYPE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "field_int32_positive",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept int32 positive value",
    ),
    SessionTestCase(
        "field_int32_negative",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": -1},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept int32 negative value",
    ),
    SessionTestCase(
        "field_int32_zero",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 0},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept int32 zero value",
    ),
    SessionTestCase(
        "field_int64",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": Int64(1)},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept int64 value",
    ),
    SessionTestCase(
        "field_int64_max",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": Int64(9_223_372_036_854_775_807)},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept int64 max value",
    ),
    SessionTestCase(
        "field_double",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1.0},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept double value",
    ),
    SessionTestCase(
        "field_double_negative",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": -1.0},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept negative double value",
    ),
    SessionTestCase(
        "field_double_zero",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 0.0},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept double zero value",
    ),
    SessionTestCase(
        "field_decimal128",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": Decimal128("1")},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept Decimal128 value",
    ),
    SessionTestCase(
        "field_bool_true",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": True},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept bool true value",
    ),
    SessionTestCase(
        "field_bool_false",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": False},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept bool false value",
    ),
    SessionTestCase(
        "field_nan",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": float("nan")},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept NaN value",
    ),
    SessionTestCase(
        "field_infinity",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": float("inf")},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept Infinity value",
    ),
    SessionTestCase(
        "field_string",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": "commitTransaction"},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept string value",
    ),
    SessionTestCase(
        "field_string_empty",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": ""},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept empty string value",
    ),
    SessionTestCase(
        "field_null",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": None},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept null value",
    ),
    SessionTestCase(
        "field_object_empty",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": {}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept empty object value",
    ),
    SessionTestCase(
        "field_object_nonempty",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": {"key": "value"}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept non-empty object value",
    ),
    SessionTestCase(
        "field_array_empty",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": []},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept empty array value",
    ),
    SessionTestCase(
        "field_array_nonempty",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": [1, 2]},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept non-empty array value",
    ),
    SessionTestCase(
        "field_binary",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": Binary(b"\x00")},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept Binary value",
    ),
    SessionTestCase(
        "field_objectid",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": ObjectId()},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept ObjectId value",
    ),
    SessionTestCase(
        "field_datetime",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept datetime value",
    ),
    SessionTestCase(
        "field_regex",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": Regex(".*")},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept Regex value",
    ),
    SessionTestCase(
        "field_timestamp",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": Timestamp(0, 0)},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept Timestamp value",
    ),
    SessionTestCase(
        "field_code",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": Code("function(){}")},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept Code value",
    ),
    SessionTestCase(
        "field_minkey",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": MinKey()},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept MinKey value",
    ),
    SessionTestCase(
        "field_maxkey",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": MaxKey()},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept MaxKey value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_TYPE_TESTS))
def test_commitTransaction_field_types(collection, test):
    """Test commitTransaction command field type acceptance in a transaction."""
    result = execute_session_command(collection, test)
    assertSuccessPartial(result, test.expected_response, msg=test.msg)
