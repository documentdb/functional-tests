"""Tests for commitTransaction txnNumber parameter validation.

Validates type acceptance for the txnNumber parameter. Per the MongoDB
documentation, txnNumber is typed as long (Int64). On a replica set,
Int64 values produce NotARetryableWriteCommand (50768) when there is no
matching transaction, while negative values produce InvalidOptions (72).
Non-Int64 numeric types and non-numeric types produce TypeMismatch. Null
is treated as omitted (falls through to NoSuchTransaction).
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
    INVALID_OPTIONS_ERROR,
    NOT_A_RETRYABLE_WRITE_COMMAND_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(change_streams=True)]


# Property [txnNumber Int64 Acceptance]: Int64 values are accepted for txnNumber.
TXN_NUMBER_INT64_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "txn_number_int64_positive",
        command={"commitTransaction": 1, "txnNumber": Int64(1)},
        error_code=NOT_A_RETRYABLE_WRITE_COMMAND_ERROR,
        msg="commitTransaction should accept txnNumber:Int64(1) and fail",
    ),
    CommandTestCase(
        "txn_number_int64_zero",
        command={"commitTransaction": 1, "txnNumber": Int64(0)},
        error_code=NOT_A_RETRYABLE_WRITE_COMMAND_ERROR,
        msg="commitTransaction should accept txnNumber:Int64(0) and fail",
    ),
    CommandTestCase(
        "txn_number_int64_max",
        command={"commitTransaction": 1, "txnNumber": Int64(9_223_372_036_854_775_807)},
        error_code=NOT_A_RETRYABLE_WRITE_COMMAND_ERROR,
        msg="commitTransaction should accept txnNumber:Int64 max value",
    ),
    CommandTestCase(
        "txn_number_int64_negative",
        command={"commitTransaction": 1, "txnNumber": Int64(-1)},
        error_code=INVALID_OPTIONS_ERROR,
        msg="commitTransaction should reject negative txnNumber with InvalidOptions",
    ),
]

# Property [txnNumber Type Strictness]: non-Int64 types are rejected with TypeMismatch.
TXN_NUMBER_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "txn_number_int32",
        command={"commitTransaction": 1, "txnNumber": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:int32 as wrong type",
    ),
    CommandTestCase(
        "txn_number_double_whole",
        command={"commitTransaction": 1, "txnNumber": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:double (whole) as wrong type",
    ),
    CommandTestCase(
        "txn_number_double_fractional",
        command={"commitTransaction": 1, "txnNumber": 1.5},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:double (fractional) as wrong type",
    ),
    CommandTestCase(
        "txn_number_decimal128",
        command={"commitTransaction": 1, "txnNumber": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:Decimal128 as wrong type",
    ),
    CommandTestCase(
        "txn_number_string",
        command={"commitTransaction": 1, "txnNumber": "1"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:string as wrong type",
    ),
    CommandTestCase(
        "txn_number_bool",
        command={"commitTransaction": 1, "txnNumber": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:bool as wrong type",
    ),
    CommandTestCase(
        "txn_number_object",
        command={"commitTransaction": 1, "txnNumber": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:{} (object) as wrong type",
    ),
    CommandTestCase(
        "txn_number_array",
        command={"commitTransaction": 1, "txnNumber": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject txnNumber:[] (array) as wrong type",
    ),
]

# Property [txnNumber Null Handling]: null txnNumber is treated as omitted.
TXN_NUMBER_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "txn_number_null",
        command={"commitTransaction": 1, "txnNumber": None},
        error_code=COMMAND_FAILED_ERROR,
        msg="commitTransaction should treat txnNumber:null as omitted",
    ),
]

TXN_NUMBER_TESTS: list[CommandTestCase] = (
    TXN_NUMBER_INT64_TESTS + TXN_NUMBER_TYPE_REJECTION_TESTS + TXN_NUMBER_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TXN_NUMBER_TESTS))
def test_commitTransaction_txn_number_error(collection, test):
    """Test commitTransaction txnNumber parameter validation."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
