"""Tests for abortTransaction txnNumber parameter validation.

Validates type acceptance for the txnNumber parameter. Per the MongoDB
documentation, txnNumber is typed as long (Int64). Int64 values produce
IllegalOperation because the session has no matching transaction. Non-Int64
numeric types and non-numeric types produce TypeMismatch. Null is treated
as omitted (falls through to NoSuchTransaction).
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_FAILED_ERROR,
    ILLEGAL_OPERATION_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [txnNumber Int64 Acceptance]: Int64 values are accepted for txnNumber.
TXN_NUMBER_INT64_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "txn_number_int64_positive",
        command={"abortTransaction": 1, "txnNumber": Int64(1)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction should accept txnNumber:Int64(1) and fail with IllegalOperation",
    ),
    CommandTestCase(
        "txn_number_int64_zero",
        command={"abortTransaction": 1, "txnNumber": Int64(0)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction should accept txnNumber:Int64(0) and fail with IllegalOperation",
    ),
    CommandTestCase(
        "txn_number_int64_max",
        command={"abortTransaction": 1, "txnNumber": Int64(9_223_372_036_854_775_807)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction should accept txnNumber:Int64 max value",
    ),
    CommandTestCase(
        "txn_number_int64_negative",
        command={"abortTransaction": 1, "txnNumber": Int64(-1)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction should reject negative txnNumber with IllegalOperation",
    ),
]

# Property [txnNumber Type Strictness]: non-Int64 types are rejected with TypeMismatch.
TXN_NUMBER_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "txn_number_int32",
        command={"abortTransaction": 1, "txnNumber": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:int32 as wrong type",
    ),
    CommandTestCase(
        "txn_number_double_whole",
        command={"abortTransaction": 1, "txnNumber": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:double (whole) as wrong type",
    ),
    CommandTestCase(
        "txn_number_double_fractional",
        command={"abortTransaction": 1, "txnNumber": 1.5},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:double (fractional) as wrong type",
    ),
    CommandTestCase(
        "txn_number_decimal128",
        command={"abortTransaction": 1, "txnNumber": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:Decimal128 as wrong type",
    ),
    CommandTestCase(
        "txn_number_string",
        command={"abortTransaction": 1, "txnNumber": "1"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:string as wrong type",
    ),
    CommandTestCase(
        "txn_number_bool",
        command={"abortTransaction": 1, "txnNumber": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:bool as wrong type",
    ),
    CommandTestCase(
        "txn_number_object",
        command={"abortTransaction": 1, "txnNumber": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:{} (object) as wrong type",
    ),
    CommandTestCase(
        "txn_number_array",
        command={"abortTransaction": 1, "txnNumber": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="abortTransaction should reject txnNumber:[] (array) as wrong type",
    ),
]

# Property [txnNumber Null Handling]: null txnNumber is treated as omitted.
TXN_NUMBER_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "txn_number_null",
        command={"abortTransaction": 1, "txnNumber": None},
        error_code=COMMAND_FAILED_ERROR,
        msg="abortTransaction should treat txnNumber:null as omitted",
    ),
]

TXN_NUMBER_TESTS: list[CommandTestCase] = (
    TXN_NUMBER_INT64_TESTS + TXN_NUMBER_TYPE_REJECTION_TESTS + TXN_NUMBER_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TXN_NUMBER_TESTS))
def test_abortTransaction_txn_number_error(collection, test):
    """Test abortTransaction txnNumber error cases."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
