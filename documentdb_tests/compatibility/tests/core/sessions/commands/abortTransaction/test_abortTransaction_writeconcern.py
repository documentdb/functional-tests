"""Tests for abortTransaction writeConcern parameter validation.

Validates type acceptance for writeConcern (must be a document), and type and
value acceptance for sub-fields w, j, and wtimeout.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    NO_SUCH_TRANSACTION_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [writeConcern Document Acceptance]: writeConcern accepts document values.
WRITECONCERN_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "writeconcern_doc_w1",
        command={"abortTransaction": 1, "writeConcern": {"w": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern document with w:1",
    ),
    SessionCommandTestCase(
        "writeconcern_empty_doc",
        command={"abortTransaction": 1, "writeConcern": {}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept empty writeConcern document",
    ),
    SessionCommandTestCase(
        "writeconcern_null",
        command={"abortTransaction": 1, "writeConcern": None},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern:null",
    ),
    SessionCommandTestCase(
        "wc_combined_w_j_wtimeout",
        command={
            "abortTransaction": 1,
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
        },
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept combined w + j + wtimeout",
    ),
    SessionCommandTestCase(
        "wc_w0_j_true",
        command={"abortTransaction": 1, "writeConcern": {"w": 0, "j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept conflicting w:0 with j:true",
    ),
    SessionCommandTestCase(
        "wc_fsync_true",
        command={"abortTransaction": 1, "writeConcern": {"fsync": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept legacy writeConcern.fsync:true",
    ),
]

# Property [writeConcern Type Rejection]: non-document types are rejected with TypeMismatch.
WRITECONCERN_TYPE_REJECTION_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "writeconcern_string",
        command={"abortTransaction": 1, "writeConcern": "majority"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:string as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_int32",
        command={"abortTransaction": 1, "writeConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:int32 as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_int64",
        command={"abortTransaction": 1, "writeConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Int64 as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_double",
        command={"abortTransaction": 1, "writeConcern": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:double as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_decimal128",
        command={"abortTransaction": 1, "writeConcern": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Decimal128 as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_bool_true",
        command={"abortTransaction": 1, "writeConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:true as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_bool_false",
        command={"abortTransaction": 1, "writeConcern": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:false as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_array_empty",
        command={"abortTransaction": 1, "writeConcern": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:[] as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_array_nonempty",
        command={"abortTransaction": 1, "writeConcern": [{"w": 1}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:[{w:1}] as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_binary",
        command={"abortTransaction": 1, "writeConcern": Binary(b"\x00")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Binary as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_objectid",
        command={"abortTransaction": 1, "writeConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:ObjectId as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_datetime",
        command={"abortTransaction": 1, "writeConcern": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:datetime as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_regex",
        command={"abortTransaction": 1, "writeConcern": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Regex as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_timestamp",
        command={"abortTransaction": 1, "writeConcern": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Timestamp as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_code",
        command={"abortTransaction": 1, "writeConcern": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:Code as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_minkey",
        command={"abortTransaction": 1, "writeConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:MinKey as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_maxkey",
        command={"abortTransaction": 1, "writeConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern:MaxKey as wrong type",
    ),
]

# Property [w Accepted Values]: w accepts int and string "majority" values.
W_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "w_int32_one",
        command={"abortTransaction": 1, "writeConcern": {"w": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:1",
    ),
    SessionCommandTestCase(
        "w_int32_zero",
        command={"abortTransaction": 1, "writeConcern": {"w": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:0 (unacknowledged)",
    ),
    SessionCommandTestCase(
        "w_majority",
        command={"abortTransaction": 1, "writeConcern": {"w": "majority"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:'majority'",
    ),
    SessionCommandTestCase(
        "w_int64",
        command={"abortTransaction": 1, "writeConcern": {"w": Int64(1)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:Int64(1)",
    ),
    SessionCommandTestCase(
        "w_double_whole",
        command={"abortTransaction": 1, "writeConcern": {"w": 1.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:1.0",
    ),
    SessionCommandTestCase(
        "w_double_fractional",
        command={"abortTransaction": 1, "writeConcern": {"w": 1.5}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:1.5",
    ),
    SessionCommandTestCase(
        "w_decimal128",
        command={"abortTransaction": 1, "writeConcern": {"w": Decimal128("1")}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:Decimal128('1')",
    ),
]

# Property [w Invalid Values]: invalid w values are rejected with BadValue or FailedToParse.
W_INVALID_VALUE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "w_custom_tag",
        command={"abortTransaction": 1, "writeConcern": {"w": "myTag"}},
        error_code=BAD_VALUE_ERROR,
        msg="abortTransaction should reject writeConcern.w:'myTag' with BadValue",
    ),
    SessionCommandTestCase(
        "w_empty_string",
        command={"abortTransaction": 1, "writeConcern": {"w": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="abortTransaction should reject writeConcern.w:'' with BadValue",
    ),
    SessionCommandTestCase(
        "w_null",
        command={"abortTransaction": 1, "writeConcern": {"w": None}},
        error_code=BAD_VALUE_ERROR,
        msg="abortTransaction should reject writeConcern.w:null with BadValue",
    ),
    SessionCommandTestCase(
        "w_negative_int",
        command={"abortTransaction": 1, "writeConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:-1 with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_int32_max",
        command={"abortTransaction": 1, "writeConcern": {"w": 2_147_483_647}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:INT32_MAX with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_bool_false",
        command={"abortTransaction": 1, "writeConcern": {"w": False}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:false with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_bool_true",
        command={"abortTransaction": 1, "writeConcern": {"w": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:true with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_object",
        command={"abortTransaction": 1, "writeConcern": {"w": {}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:{} with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_array",
        command={"abortTransaction": 1, "writeConcern": {"w": []}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.w:[] with FailedToParse",
    ),
]

# Property [j Accepted Values]: j accepts boolean and numeric types.
J_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "j_bool_true",
        command={"abortTransaction": 1, "writeConcern": {"j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:true",
    ),
    SessionCommandTestCase(
        "j_bool_false",
        command={"abortTransaction": 1, "writeConcern": {"j": False}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:false",
    ),
    SessionCommandTestCase(
        "j_int32_one",
        command={"abortTransaction": 1, "writeConcern": {"j": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:1 (coerced to true)",
    ),
    SessionCommandTestCase(
        "j_int32_zero",
        command={"abortTransaction": 1, "writeConcern": {"j": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:0 (coerced to false)",
    ),
    SessionCommandTestCase(
        "j_null",
        command={"abortTransaction": 1, "writeConcern": {"j": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:null",
    ),
]

# Property [j Type Rejection]: non-boolean non-numeric types are rejected with TypeMismatch.
J_TYPE_REJECTION_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "j_string",
        command={"abortTransaction": 1, "writeConcern": {"j": "true"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern.j:'true' as wrong type",
    ),
    SessionCommandTestCase(
        "j_object",
        command={"abortTransaction": 1, "writeConcern": {"j": {}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern.j:{} as wrong type",
    ),
    SessionCommandTestCase(
        "j_array",
        command={"abortTransaction": 1, "writeConcern": {"j": []}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject writeConcern.j:[] as wrong type",
    ),
]

# Property [wtimeout Accepted Values]: wtimeout accepts numeric types broadly.
WTIMEOUT_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "wtimeout_int32_positive",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": 1000}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:1000",
    ),
    SessionCommandTestCase(
        "wtimeout_int32_zero",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:0 (no timeout)",
    ),
    SessionCommandTestCase(
        "wtimeout_int64",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": Int64(1000)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:Int64(1000)",
    ),
    SessionCommandTestCase(
        "wtimeout_double_whole",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": 1000.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:1000.0",
    ),
    SessionCommandTestCase(
        "wtimeout_negative",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": -1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:-1",
    ),
    SessionCommandTestCase(
        "wtimeout_string",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": "1000"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:'1000'",
    ),
    SessionCommandTestCase(
        "wtimeout_bool",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:true",
    ),
    SessionCommandTestCase(
        "wtimeout_null",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:null",
    ),
    SessionCommandTestCase(
        "wtimeout_object",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": {}}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:{}",
    ),
    SessionCommandTestCase(
        "wtimeout_array",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": []}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:[]",
    ),
]

# Property [wtimeout Overflow]: Int64 max value overflows and produces FailedToParse.
WTIMEOUT_OVERFLOW_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "wtimeout_int64_max",
        command={
            "abortTransaction": 1,
            "writeConcern": {"wtimeout": Int64(9_223_372_036_854_775_807)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="abortTransaction should reject writeConcern.wtimeout:Int64 max with FailedToParse",
    ),
]

WRITECONCERN_TESTS: list[SessionCommandTestCase] = (
    WRITECONCERN_ACCEPTANCE_TESTS
    + WRITECONCERN_TYPE_REJECTION_TESTS
    + W_ACCEPTANCE_TESTS
    + W_INVALID_VALUE_TESTS
    + J_ACCEPTANCE_TESTS
    + J_TYPE_REJECTION_TESTS
    + WTIMEOUT_ACCEPTANCE_TESTS
    + WTIMEOUT_OVERFLOW_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITECONCERN_TESTS))
def test_abortTransaction_writeconcern(collection, test):
    """Test abortTransaction writeConcern parameter validation."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
