"""Tests for abortTransaction writeConcern parameter error cases.

Validates that invalid writeConcern types and sub-field values are rejected
with the appropriate error codes.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_FAILED_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(change_streams=True)]

# Property [writeConcern Type Rejection]: non-document types are rejected with TypeMismatch.
WRITECONCERN_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_string",
        command={"abortTransaction": 1, "writeConcern": "majority"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:string as wrong type",
    ),
    CommandTestCase(
        "writeconcern_int32",
        command={"abortTransaction": 1, "writeConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:int32 as wrong type",
    ),
    CommandTestCase(
        "writeconcern_int64",
        command={"abortTransaction": 1, "writeConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Int64 as wrong type",
    ),
    CommandTestCase(
        "writeconcern_double",
        command={"abortTransaction": 1, "writeConcern": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:double as wrong type",
    ),
    CommandTestCase(
        "writeconcern_decimal128",
        command={"abortTransaction": 1, "writeConcern": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Decimal128 as wrong type",
    ),
    CommandTestCase(
        "writeconcern_bool_true",
        command={"abortTransaction": 1, "writeConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:true as wrong type",
    ),
    CommandTestCase(
        "writeconcern_bool_false",
        command={"abortTransaction": 1, "writeConcern": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:false as wrong type",
    ),
    CommandTestCase(
        "writeconcern_array_empty",
        command={"abortTransaction": 1, "writeConcern": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:[] as wrong type",
    ),
    CommandTestCase(
        "writeconcern_array_nonempty",
        command={"abortTransaction": 1, "writeConcern": [{"w": 1}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:[{w:1}] as wrong type",
    ),
    CommandTestCase(
        "writeconcern_binary",
        command={"abortTransaction": 1, "writeConcern": Binary(b"\x00")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Binary as wrong type",
    ),
    CommandTestCase(
        "writeconcern_objectid",
        command={"abortTransaction": 1, "writeConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:ObjectId as wrong type",
    ),
    CommandTestCase(
        "writeconcern_datetime",
        command={"abortTransaction": 1, "writeConcern": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:datetime as wrong type",
    ),
    CommandTestCase(
        "writeconcern_regex",
        command={"abortTransaction": 1, "writeConcern": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Regex as wrong type",
    ),
    CommandTestCase(
        "writeconcern_timestamp",
        command={"abortTransaction": 1, "writeConcern": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Timestamp as wrong type",
    ),
    CommandTestCase(
        "writeconcern_code",
        command={"abortTransaction": 1, "writeConcern": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Code as wrong type",
    ),
    CommandTestCase(
        "writeconcern_minkey",
        command={"abortTransaction": 1, "writeConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:MinKey as wrong type",
    ),
    CommandTestCase(
        "writeconcern_maxkey",
        command={"abortTransaction": 1, "writeConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:MaxKey as wrong type",
    ),
]

# Property [w Invalid Values]: invalid w values are rejected with CommandFailed or FailedToParse.
W_INVALID_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_custom_tag",
        command={"abortTransaction": 1, "writeConcern": {"w": "myTag"}},
        error_code=COMMAND_FAILED_ERROR,
        msg="abortTransaction should reject writeConcern.w:'myTag' with CommandFailed",
    ),
    CommandTestCase(
        "w_empty_string",
        command={"abortTransaction": 1, "writeConcern": {"w": ""}},
        error_code=COMMAND_FAILED_ERROR,
        msg="abortTransaction should reject writeConcern.w:'' with CommandFailed",
    ),
    CommandTestCase(
        "w_null",
        command={"abortTransaction": 1, "writeConcern": {"w": None}},
        error_code=COMMAND_FAILED_ERROR,
        msg="abortTransaction should reject writeConcern.w:null with CommandFailed",
    ),
    CommandTestCase(
        "w_negative_int",
        command={"abortTransaction": 1, "writeConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:-1 with FailedToParse",
    ),
    CommandTestCase(
        "w_int32_max",
        command={"abortTransaction": 1, "writeConcern": {"w": 2_147_483_647}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:INT32_MAX with FailedToParse",
    ),
    CommandTestCase(
        "w_bool_false",
        command={"abortTransaction": 1, "writeConcern": {"w": False}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:false with FailedToParse",
    ),
    CommandTestCase(
        "w_bool_true",
        command={"abortTransaction": 1, "writeConcern": {"w": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:true with FailedToParse",
    ),
    CommandTestCase(
        "w_object",
        command={"abortTransaction": 1, "writeConcern": {"w": {}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:{} with FailedToParse",
    ),
    CommandTestCase(
        "w_array",
        command={"abortTransaction": 1, "writeConcern": {"w": []}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:[] with FailedToParse",
    ),
]

# Property [j Type Rejection]: non-boolean non-numeric types are rejected with TypeMismatch.
J_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "j_string",
        command={"abortTransaction": 1, "writeConcern": {"j": "true"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern.j:'true' as wrong type",
    ),
    CommandTestCase(
        "j_object",
        command={"abortTransaction": 1, "writeConcern": {"j": {}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern.j:{} as wrong type",
    ),
    CommandTestCase(
        "j_array",
        command={"abortTransaction": 1, "writeConcern": {"j": []}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern.j:[] as wrong type",
    ),
]

# Property [wtimeout Overflow]: Int64 max value overflows and produces FailedToParse.
WTIMEOUT_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_int64_max",
        command={
            "abortTransaction": 1,
            "writeConcern": {"wtimeout": Int64(9_223_372_036_854_775_807)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.wtimeout:Int64 max with FailedToParse",
    ),
]

WRITECONCERN_ERROR_TESTS: list[CommandTestCase] = (
    WRITECONCERN_TYPE_REJECTION_TESTS
    + W_INVALID_VALUE_TESTS
    + J_TYPE_REJECTION_TESTS
    + WTIMEOUT_OVERFLOW_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITECONCERN_ERROR_TESTS))
def test_abortTransaction_writeconcern_error(collection, test):
    """Test abortTransaction writeConcern parameter error cases."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
