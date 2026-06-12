"""Tests for commitTransaction autocommit parameter validation.

Validates type and value acceptance for the autocommit parameter. Per the
MongoDB documentation, autocommit must be literal boolean false. Boolean true
produces InvalidOptions, non-boolean types produce TypeMismatch, and null is
treated as omitted (falls through to NoSuchTransaction).
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
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [autocommit Boolean Values]: autocommit accepts only boolean values.
AUTOCOMMIT_BOOLEAN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "autocommit_bool_false",
        command={"commitTransaction": 1, "autocommit": False},
        error_code=INVALID_OPTIONS_ERROR,
        msg="commitTransaction should reject autocommit:false outside txn with InvalidOptions",
    ),
    CommandTestCase(
        "autocommit_bool_true",
        command={"commitTransaction": 1, "autocommit": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="commitTransaction should reject autocommit:true with InvalidOptions",
    ),
]

# Property [autocommit Type Strictness]: non-boolean types are rejected with TypeMismatch.
AUTOCOMMIT_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "autocommit_int32_zero",
        command={"commitTransaction": 1, "autocommit": 0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:0 (int32) as wrong type",
    ),
    CommandTestCase(
        "autocommit_int32_one",
        command={"commitTransaction": 1, "autocommit": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:1 (int32) as wrong type",
    ),
    CommandTestCase(
        "autocommit_int64_zero",
        command={"commitTransaction": 1, "autocommit": Int64(0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:Int64(0) as wrong type",
    ),
    CommandTestCase(
        "autocommit_double_zero",
        command={"commitTransaction": 1, "autocommit": 0.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:0.0 as wrong type",
    ),
    CommandTestCase(
        "autocommit_decimal128_zero",
        command={"commitTransaction": 1, "autocommit": Decimal128("0")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:Decimal128('0') as wrong type",
    ),
    CommandTestCase(
        "autocommit_string",
        command={"commitTransaction": 1, "autocommit": "false"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:'false' (string) as wrong type",
    ),
    CommandTestCase(
        "autocommit_object",
        command={"commitTransaction": 1, "autocommit": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:{} (object) as wrong type",
    ),
    CommandTestCase(
        "autocommit_array",
        command={"commitTransaction": 1, "autocommit": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject autocommit:[] (array) as wrong type",
    ),
]

# Property [autocommit Null Handling]: null autocommit is treated as omitted.
AUTOCOMMIT_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "autocommit_null",
        command={"commitTransaction": 1, "autocommit": None},
        error_code=COMMAND_FAILED_ERROR,
        msg="commitTransaction should treat autocommit:null as omitted",
    ),
]

AUTOCOMMIT_TESTS: list[CommandTestCase] = (
    AUTOCOMMIT_BOOLEAN_TESTS + AUTOCOMMIT_TYPE_REJECTION_TESTS + AUTOCOMMIT_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AUTOCOMMIT_TESTS))
def test_commitTransaction_autocommit_error(collection, test):
    """Test commitTransaction autocommit parameter validation."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
