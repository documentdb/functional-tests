"""Tests for abortTransaction command field type acceptance.

Validates that the abortTransaction command's primary field accepts all BSON
types. All types produce NoSuchTransaction because no transaction is active,
confirming the field value itself is not type-checked.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [Field Type Acceptance]: the command field accepts any BSON type.
FIELD_TYPE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "field_int32_positive",
        command={"abortTransaction": 1},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept int32 positive value",
    ),
    SessionCommandTestCase(
        "field_int32_negative",
        command={"abortTransaction": -1},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept int32 negative value",
    ),
    SessionCommandTestCase(
        "field_int32_zero",
        command={"abortTransaction": 0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept int32 zero value",
    ),
    SessionCommandTestCase(
        "field_int64",
        command={"abortTransaction": Int64(1)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept int64 value",
    ),
    SessionCommandTestCase(
        "field_int64_max",
        command={"abortTransaction": Int64(9_223_372_036_854_775_807)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept int64 max value",
    ),
    SessionCommandTestCase(
        "field_double",
        command={"abortTransaction": 1.0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept double value",
    ),
    SessionCommandTestCase(
        "field_double_negative",
        command={"abortTransaction": -1.0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept negative double value",
    ),
    SessionCommandTestCase(
        "field_double_zero",
        command={"abortTransaction": 0.0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept double zero value",
    ),
    SessionCommandTestCase(
        "field_decimal128",
        command={"abortTransaction": Decimal128("1")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept Decimal128 value",
    ),
    SessionCommandTestCase(
        "field_bool_true",
        command={"abortTransaction": True},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept bool true value",
    ),
    SessionCommandTestCase(
        "field_bool_false",
        command={"abortTransaction": False},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept bool false value",
    ),
    SessionCommandTestCase(
        "field_nan",
        command={"abortTransaction": float("nan")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept NaN value",
    ),
    SessionCommandTestCase(
        "field_infinity",
        command={"abortTransaction": float("inf")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept Infinity value",
    ),
    SessionCommandTestCase(
        "field_string",
        command={"abortTransaction": "abortTransaction"},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept string value",
    ),
    SessionCommandTestCase(
        "field_string_empty",
        command={"abortTransaction": ""},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept empty string value",
    ),
    SessionCommandTestCase(
        "field_null",
        command={"abortTransaction": None},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept null value",
    ),
    SessionCommandTestCase(
        "field_object_empty",
        command={"abortTransaction": {}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept empty object value",
    ),
    SessionCommandTestCase(
        "field_object_nonempty",
        command={"abortTransaction": {"key": "value"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept non-empty object value",
    ),
    SessionCommandTestCase(
        "field_array_empty",
        command={"abortTransaction": []},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept empty array value",
    ),
    SessionCommandTestCase(
        "field_array_nonempty",
        command={"abortTransaction": [1, 2]},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept non-empty array value",
    ),
    SessionCommandTestCase(
        "field_binary",
        command={"abortTransaction": Binary(b"\x00")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept Binary value",
    ),
    SessionCommandTestCase(
        "field_objectid",
        command={"abortTransaction": ObjectId()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept ObjectId value",
    ),
    SessionCommandTestCase(
        "field_datetime",
        command={"abortTransaction": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept datetime value",
    ),
    SessionCommandTestCase(
        "field_regex",
        command={"abortTransaction": Regex(".*")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept Regex value",
    ),
    SessionCommandTestCase(
        "field_timestamp",
        command={"abortTransaction": Timestamp(0, 0)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept Timestamp value",
    ),
    SessionCommandTestCase(
        "field_code",
        command={"abortTransaction": Code("function(){}")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept Code value",
    ),
    SessionCommandTestCase(
        "field_minkey",
        command={"abortTransaction": MinKey()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept MinKey value",
    ),
    SessionCommandTestCase(
        "field_maxkey",
        command={"abortTransaction": MaxKey()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept MaxKey value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_TYPE_TESTS))
def test_abortTransaction_field_types(collection, test):
    """Test abortTransaction command field type acceptance."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
