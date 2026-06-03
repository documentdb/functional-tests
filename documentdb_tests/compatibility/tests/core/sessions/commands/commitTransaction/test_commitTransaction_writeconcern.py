"""Tests for commitTransaction writeConcern parameter validation.

Validates type acceptance for writeConcern (must be a document), and type and
value acceptance for sub-fields w, j, and wtimeout.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
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
WRITECONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_doc_w1",
        command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern document with w:1",
    ),
    CommandTestCase(
        "writeconcern_empty_doc",
        command={"commitTransaction": 1, "writeConcern": {}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept empty writeConcern document",
    ),
    CommandTestCase(
        "writeconcern_null",
        command={"commitTransaction": 1, "writeConcern": None},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern:null",
    ),
    CommandTestCase(
        "wc_combined_w_j_wtimeout",
        command={
            "commitTransaction": 1,
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
        },
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept combined w + j + wtimeout",
    ),
    CommandTestCase(
        "wc_w0_j_true",
        command={"commitTransaction": 1, "writeConcern": {"w": 0, "j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept conflicting w:0 with j:true",
    ),
    CommandTestCase(
        "wc_fsync_true",
        command={"commitTransaction": 1, "writeConcern": {"fsync": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept legacy writeConcern.fsync:true",
    ),
]

# Property [writeConcern Type Rejection]: non-document types are rejected with TypeMismatch.
WRITECONCERN_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_string",
        command={"commitTransaction": 1, "writeConcern": "majority"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:string as wrong type",
    ),
    CommandTestCase(
        "writeconcern_int32",
        command={"commitTransaction": 1, "writeConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:int32 as wrong type",
    ),
    CommandTestCase(
        "writeconcern_int64",
        command={"commitTransaction": 1, "writeConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Int64 as wrong type",
    ),
    CommandTestCase(
        "writeconcern_double",
        command={"commitTransaction": 1, "writeConcern": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:double as wrong type",
    ),
    CommandTestCase(
        "writeconcern_decimal128",
        command={"commitTransaction": 1, "writeConcern": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Decimal128 as wrong type",
    ),
    CommandTestCase(
        "writeconcern_bool_true",
        command={"commitTransaction": 1, "writeConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:true as wrong type",
    ),
    CommandTestCase(
        "writeconcern_bool_false",
        command={"commitTransaction": 1, "writeConcern": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:false as wrong type",
    ),
    CommandTestCase(
        "writeconcern_array_empty",
        command={"commitTransaction": 1, "writeConcern": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:[] as wrong type",
    ),
    CommandTestCase(
        "writeconcern_array_nonempty",
        command={"commitTransaction": 1, "writeConcern": [{"w": 1}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:[{w:1}] as wrong type",
    ),
    CommandTestCase(
        "writeconcern_binary",
        command={"commitTransaction": 1, "writeConcern": Binary(b"\x00")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Binary as wrong type",
    ),
    CommandTestCase(
        "writeconcern_objectid",
        command={"commitTransaction": 1, "writeConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:ObjectId as wrong type",
    ),
    CommandTestCase(
        "writeconcern_datetime",
        command={"commitTransaction": 1, "writeConcern": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:datetime as wrong type",
    ),
    CommandTestCase(
        "writeconcern_regex",
        command={"commitTransaction": 1, "writeConcern": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Regex as wrong type",
    ),
    CommandTestCase(
        "writeconcern_timestamp",
        command={"commitTransaction": 1, "writeConcern": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Timestamp as wrong type",
    ),
    CommandTestCase(
        "writeconcern_code",
        command={"commitTransaction": 1, "writeConcern": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Code as wrong type",
    ),
    CommandTestCase(
        "writeconcern_minkey",
        command={"commitTransaction": 1, "writeConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:MinKey as wrong type",
    ),
    CommandTestCase(
        "writeconcern_maxkey",
        command={"commitTransaction": 1, "writeConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:MaxKey as wrong type",
    ),
]

# Property [w Accepted Values]: w accepts int and string "majority" values.
W_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_int32_one",
        command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:1",
    ),
    CommandTestCase(
        "w_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"w": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:0 (unacknowledged)",
    ),
    CommandTestCase(
        "w_majority",
        command={"commitTransaction": 1, "writeConcern": {"w": "majority"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:'majority'",
    ),
    CommandTestCase(
        "w_int64",
        command={"commitTransaction": 1, "writeConcern": {"w": Int64(1)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:Int64(1)",
    ),
    CommandTestCase(
        "w_double_whole",
        command={"commitTransaction": 1, "writeConcern": {"w": 1.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:1.0",
    ),
    CommandTestCase(
        "w_double_fractional",
        command={"commitTransaction": 1, "writeConcern": {"w": 1.5}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:1.5",
    ),
    CommandTestCase(
        "w_decimal128",
        command={"commitTransaction": 1, "writeConcern": {"w": Decimal128("1")}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:Decimal128('1')",
    ),
]

# Property [w Invalid Values]: invalid w values are rejected with BadValue or FailedToParse.
W_INVALID_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_custom_tag",
        command={"commitTransaction": 1, "writeConcern": {"w": "myTag"}},
        error_code=BAD_VALUE_ERROR,
        msg="commitTransaction should reject writeConcern.w:'myTag' with BadValue",
    ),
    CommandTestCase(
        "w_empty_string",
        command={"commitTransaction": 1, "writeConcern": {"w": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="commitTransaction should reject writeConcern.w:'' with BadValue",
    ),
    CommandTestCase(
        "w_null",
        command={"commitTransaction": 1, "writeConcern": {"w": None}},
        error_code=BAD_VALUE_ERROR,
        msg="commitTransaction should reject writeConcern.w:null with BadValue",
    ),
    CommandTestCase(
        "w_negative_int",
        command={"commitTransaction": 1, "writeConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:-1 with FailedToParse",
    ),
    CommandTestCase(
        "w_int32_max",
        command={"commitTransaction": 1, "writeConcern": {"w": 2_147_483_647}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:INT32_MAX with FailedToParse",
    ),
    CommandTestCase(
        "w_bool_false",
        command={"commitTransaction": 1, "writeConcern": {"w": False}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:false with FailedToParse",
    ),
    CommandTestCase(
        "w_bool_true",
        command={"commitTransaction": 1, "writeConcern": {"w": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:true with FailedToParse",
    ),
    CommandTestCase(
        "w_object",
        command={"commitTransaction": 1, "writeConcern": {"w": {}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:{} with FailedToParse",
    ),
    CommandTestCase(
        "w_array",
        command={"commitTransaction": 1, "writeConcern": {"w": []}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:[] with FailedToParse",
    ),
]

# Property [j Accepted Values]: j accepts boolean and numeric types.
J_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "j_bool_true",
        command={"commitTransaction": 1, "writeConcern": {"j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:true",
    ),
    CommandTestCase(
        "j_bool_false",
        command={"commitTransaction": 1, "writeConcern": {"j": False}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:false",
    ),
    CommandTestCase(
        "j_int32_one",
        command={"commitTransaction": 1, "writeConcern": {"j": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:1 (coerced to true)",
    ),
    CommandTestCase(
        "j_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"j": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:0 (coerced to false)",
    ),
    CommandTestCase(
        "j_null",
        command={"commitTransaction": 1, "writeConcern": {"j": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:null",
    ),
]

# Property [j Type Rejection]: non-boolean non-numeric types are rejected with TypeMismatch.
J_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "j_string",
        command={"commitTransaction": 1, "writeConcern": {"j": "true"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern.j:'true' as wrong type",
    ),
    CommandTestCase(
        "j_object",
        command={"commitTransaction": 1, "writeConcern": {"j": {}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern.j:{} as wrong type",
    ),
    CommandTestCase(
        "j_array",
        command={"commitTransaction": 1, "writeConcern": {"j": []}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern.j:[] as wrong type",
    ),
]

# Property [wtimeout Accepted Values]: wtimeout accepts numeric types broadly.
WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_int32_positive",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:1000",
    ),
    CommandTestCase(
        "wtimeout_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:0 (no timeout)",
    ),
    CommandTestCase(
        "wtimeout_int64",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": Int64(1000)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:Int64(1000)",
    ),
    CommandTestCase(
        "wtimeout_double_whole",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:1000.0",
    ),
    CommandTestCase(
        "wtimeout_negative",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": -1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:-1",
    ),
    CommandTestCase(
        "wtimeout_string",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": "1000"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:'1000'",
    ),
    CommandTestCase(
        "wtimeout_bool",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:true",
    ),
    CommandTestCase(
        "wtimeout_null",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:null",
    ),
    CommandTestCase(
        "wtimeout_object",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": {}}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:{}",
    ),
    CommandTestCase(
        "wtimeout_array",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": []}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:[]",
    ),
]

# Property [wtimeout Overflow]: Int64 max value overflows and produces FailedToParse.
WTIMEOUT_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_int64_max",
        command={
            "commitTransaction": 1,
            "writeConcern": {"wtimeout": Int64(9_223_372_036_854_775_807)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.wtimeout:Int64 max with FailedToParse",
    ),
]

WRITECONCERN_TESTS: list[CommandTestCase] = (
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
def test_commitTransaction_writeconcern(collection, test):
    """Test commitTransaction writeConcern parameter validation."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
