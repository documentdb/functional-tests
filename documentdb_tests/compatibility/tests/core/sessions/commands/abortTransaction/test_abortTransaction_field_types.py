"""Tests for abortTransaction command field type acceptance in a real transaction.

Validates that the abortTransaction command's primary field accepts all BSON
types when issued inside an active transaction on a replica set.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]

# Property [Field Type Acceptance]: the command field accepts any BSON type.
FIELD_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "field_int32_positive",
        command={"abortTransaction": 1},
        msg="abortTransaction should accept int32 positive value",
    ),
    CommandTestCase(
        "field_int32_negative",
        command={"abortTransaction": -1},
        msg="abortTransaction should accept int32 negative value",
    ),
    CommandTestCase(
        "field_int32_zero",
        command={"abortTransaction": 0},
        msg="abortTransaction should accept int32 zero value",
    ),
    CommandTestCase(
        "field_int64",
        command={"abortTransaction": Int64(1)},
        msg="abortTransaction should accept int64 value",
    ),
    CommandTestCase(
        "field_int64_max",
        command={"abortTransaction": Int64(9_223_372_036_854_775_807)},
        msg="abortTransaction should accept int64 max value",
    ),
    CommandTestCase(
        "field_double",
        command={"abortTransaction": 1.0},
        msg="abortTransaction should accept double value",
    ),
    CommandTestCase(
        "field_double_negative",
        command={"abortTransaction": -1.0},
        msg="abortTransaction should accept negative double value",
    ),
    CommandTestCase(
        "field_double_zero",
        command={"abortTransaction": 0.0},
        msg="abortTransaction should accept double zero value",
    ),
    CommandTestCase(
        "field_decimal128",
        command={"abortTransaction": Decimal128("1")},
        msg="abortTransaction should accept Decimal128 value",
    ),
    CommandTestCase(
        "field_bool_true",
        command={"abortTransaction": True},
        msg="abortTransaction should accept bool true value",
    ),
    CommandTestCase(
        "field_bool_false",
        command={"abortTransaction": False},
        msg="abortTransaction should accept bool false value",
    ),
    CommandTestCase(
        "field_nan",
        command={"abortTransaction": float("nan")},
        msg="abortTransaction should accept NaN value",
    ),
    CommandTestCase(
        "field_infinity",
        command={"abortTransaction": float("inf")},
        msg="abortTransaction should accept Infinity value",
    ),
    CommandTestCase(
        "field_string",
        command={"abortTransaction": "abortTransaction"},
        msg="abortTransaction should accept string value",
    ),
    CommandTestCase(
        "field_string_empty",
        command={"abortTransaction": ""},
        msg="abortTransaction should accept empty string value",
    ),
    CommandTestCase(
        "field_null",
        command={"abortTransaction": None},
        msg="abortTransaction should accept null value",
    ),
    CommandTestCase(
        "field_object_empty",
        command={"abortTransaction": {}},
        msg="abortTransaction should accept empty object value",
    ),
    CommandTestCase(
        "field_object_nonempty",
        command={"abortTransaction": {"key": "value"}},
        msg="abortTransaction should accept non-empty object value",
    ),
    CommandTestCase(
        "field_array_empty",
        command={"abortTransaction": []},
        msg="abortTransaction should accept empty array value",
    ),
    CommandTestCase(
        "field_array_nonempty",
        command={"abortTransaction": [1, 2]},
        msg="abortTransaction should accept non-empty array value",
    ),
    CommandTestCase(
        "field_binary",
        command={"abortTransaction": Binary(b"\x00")},
        msg="abortTransaction should accept Binary value",
    ),
    CommandTestCase(
        "field_objectid",
        command={"abortTransaction": ObjectId()},
        msg="abortTransaction should accept ObjectId value",
    ),
    CommandTestCase(
        "field_datetime",
        command={"abortTransaction": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="abortTransaction should accept datetime value",
    ),
    CommandTestCase(
        "field_regex",
        command={"abortTransaction": Regex(".*")},
        msg="abortTransaction should accept Regex value",
    ),
    CommandTestCase(
        "field_timestamp",
        command={"abortTransaction": Timestamp(0, 0)},
        msg="abortTransaction should accept Timestamp value",
    ),
    CommandTestCase(
        "field_code",
        command={"abortTransaction": Code("function(){}")},
        msg="abortTransaction should accept Code value",
    ),
    CommandTestCase(
        "field_minkey",
        command={"abortTransaction": MinKey()},
        msg="abortTransaction should accept MinKey value",
    ),
    CommandTestCase(
        "field_maxkey",
        command={"abortTransaction": MaxKey()},
        msg="abortTransaction should accept MaxKey value",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(FIELD_TYPE_TESTS))
def test_abortTransaction_field_types(collection, test):
    """Test abortTransaction command field type acceptance in a transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = execute_admin_command(collection, test.command, session=session)
    assertSuccessPartial(result, {"ok": 1.0}, msg=test.msg)
