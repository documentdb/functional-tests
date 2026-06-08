"""Tests for commitTransaction comment parameter type acceptance in a real transaction.

Validates that the comment parameter accepts any BSON type when
commitTransaction is issued inside an active transaction on a replica set.
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

pytestmark = [pytest.mark.admin, pytest.mark.replica_set]

_INSERT_OP = [SessionOperation(op=SessionOp.INSERT, document={"_id": 1})]
_OK_RESPONSE = {"ok": 1.0}


# ---------------------------------------------------------------------------
# Property [comment Type Acceptance]: comment accepts any BSON type.
# ---------------------------------------------------------------------------

COMMENT_TYPE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "comment_string",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": "test comment"},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:string",
    ),
    SessionTestCase(
        "comment_string_empty",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": ""},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:empty string",
    ),
    SessionTestCase(
        "comment_int32",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": 42},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:int32",
    ),
    SessionTestCase(
        "comment_int64",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": Int64(42)},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:Int64",
    ),
    SessionTestCase(
        "comment_double",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": 3.14},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:double",
    ),
    SessionTestCase(
        "comment_decimal128",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": Decimal128("1.5")},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:Decimal128",
    ),
    SessionTestCase(
        "comment_bool_true",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": True},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:true",
    ),
    SessionTestCase(
        "comment_bool_false",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": False},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:false",
    ),
    SessionTestCase(
        "comment_null",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": None},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:null",
    ),
    SessionTestCase(
        "comment_object",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": {"key": "value"}},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:object",
    ),
    SessionTestCase(
        "comment_object_empty",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": {}},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:empty object",
    ),
    SessionTestCase(
        "comment_array",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": [1, 2, 3]},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:array",
    ),
    SessionTestCase(
        "comment_array_empty",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": []},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:empty array",
    ),
    SessionTestCase(
        "comment_objectid",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": ObjectId()},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:ObjectId",
    ),
    SessionTestCase(
        "comment_datetime",
        ops=_INSERT_OP,
        commit_command={
            "commitTransaction": 1,
            "comment": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:datetime",
    ),
    SessionTestCase(
        "comment_binary",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": Binary(b"\x00")},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:Binary",
    ),
    SessionTestCase(
        "comment_regex",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": Regex(".*")},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:Regex",
    ),
    SessionTestCase(
        "comment_timestamp",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": Timestamp(0, 0)},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:Timestamp",
    ),
    SessionTestCase(
        "comment_minkey",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": MinKey()},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:MinKey",
    ),
    SessionTestCase(
        "comment_maxkey",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": MaxKey()},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:MaxKey",
    ),
    SessionTestCase(
        "comment_code",
        ops=_INSERT_OP,
        commit_command={"commitTransaction": 1, "comment": Code("function(){}")},
        expected_response=_OK_RESPONSE,
        msg="commitTransaction should accept comment:Code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMENT_TYPE_TESTS))
def test_commitTransaction_comment(collection, test):
    """Test commitTransaction comment parameter type acceptance in a transaction."""
    result = execute_session_command(collection, test)
    assertSuccessPartial(result, test.expected_response, msg=test.msg)
