"""
Tests for $all query operator error cases.

Validates that $all rejects invalid arguments.

"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INVALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_arg",
        filter={"a": {"$all": "x"}},
        error_code=BAD_VALUE_ERROR,
        msg="String argument should error",
    ),
    QueryTestCase(
        id="null_arg",
        filter={"a": {"$all": None}},
        error_code=BAD_VALUE_ERROR,
        msg="Null argument should error",
    ),
    QueryTestCase(
        id="int_arg",
        filter={"a": {"$all": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="Integer argument should error",
    ),
    QueryTestCase(
        id="object_arg",
        filter={"a": {"$all": {}}},
        error_code=BAD_VALUE_ERROR,
        msg="Object argument should error",
    ),
    QueryTestCase(
        id="bool_arg",
        filter={"a": {"$all": True}},
        error_code=BAD_VALUE_ERROR,
        msg="Boolean argument should error",
    ),
    QueryTestCase(
        id="double_arg",
        filter={"a": {"$all": 1.5}},
        error_code=BAD_VALUE_ERROR,
        msg="Double argument should error",
    ),
    QueryTestCase(
        id="long_arg",
        filter={"a": {"$all": Int64(1)}},
        error_code=BAD_VALUE_ERROR,
        msg="Long argument should error",
    ),
    QueryTestCase(
        id="decimal128_arg",
        filter={"a": {"$all": Decimal128("1")}},
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 argument should error",
    ),
    QueryTestCase(
        id="date_arg",
        filter={"a": {"$all": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        error_code=BAD_VALUE_ERROR,
        msg="Date argument should error",
    ),
    QueryTestCase(
        id="objectid_arg",
        filter={"a": {"$all": ObjectId()}},
        error_code=BAD_VALUE_ERROR,
        msg="ObjectId argument should error",
    ),
    QueryTestCase(
        id="regex_arg",
        filter={"a": {"$all": Regex("pattern")}},
        error_code=BAD_VALUE_ERROR,
        msg="Regex argument should error",
    ),
    QueryTestCase(
        id="bindata_arg",
        filter={"a": {"$all": Binary(b"")}},
        error_code=BAD_VALUE_ERROR,
        msg="BinData argument should error",
    ),
    QueryTestCase(
        id="timestamp_arg",
        filter={"a": {"$all": Timestamp(0, 0)}},
        error_code=BAD_VALUE_ERROR,
        msg="Timestamp argument should error",
    ),
    QueryTestCase(
        id="javascript_arg",
        filter={"a": {"$all": Code("return 1")}},
        error_code=BAD_VALUE_ERROR,
        msg="JavaScript argument should error",
    ),
    QueryTestCase(
        id="minkey_arg",
        filter={"a": {"$all": MinKey()}},
        error_code=BAD_VALUE_ERROR,
        msg="MinKey argument should error",
    ),
    QueryTestCase(
        id="maxkey_arg",
        filter={"a": {"$all": MaxKey()}},
        error_code=BAD_VALUE_ERROR,
        msg="MaxKey argument should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_ARGUMENT_TESTS))
def test_all_invalid_arguments(collection, test):
    """Test $all rejects non-array arguments with error code 2 (BadValue)."""
    collection.insert_many([{"_id": 1, "a": [1]}])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code)
