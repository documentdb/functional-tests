"""
Tests for $and error cases and invalid argument handling.

Tests that $and returns correct error codes for malformed expressions,
invalid argument types, and invalid element types at various positions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array",
        filter={"$and": []},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with empty array errors",
    ),
    QueryTestCase(
        id="not_array_object",
        filter={"$and": {"a": 1}},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with object instead of array errors",
    ),
    QueryTestCase(
        id="not_array_int",
        filter={"$and": 1},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with integer errors",
    ),
    QueryTestCase(
        id="not_array_string",
        filter={"$and": "string"},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with string errors",
    ),
    QueryTestCase(
        id="not_array_null",
        filter={"$and": None},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with null errors",
    ),
    QueryTestCase(
        id="element_int",
        filter={"$and": [1]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with integer element errors",
    ),
    QueryTestCase(
        id="element_string",
        filter={"$and": ["string"]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with string element errors",
    ),
    QueryTestCase(
        id="element_null",
        filter={"$and": [None]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with null element errors",
    ),
    QueryTestCase(
        id="element_bool",
        filter={"$and": [True]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with boolean element errors",
    ),
    QueryTestCase(
        id="non_object_position_0",
        filter={"$and": [1, {"a": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with non-object at position 0 errors",
    ),
    QueryTestCase(
        id="non_object_position_1",
        filter={"$and": [{"a": 1}, 1]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with non-object at position 1 errors",
    ),
    QueryTestCase(
        id="non_object_position_2",
        filter={"$and": [{"a": 1}, {"b": 2}, 1]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with non-object at position 2 errors",
    ),
    QueryTestCase(
        id="null_position_0",
        filter={"$and": [None, {"a": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with null at position 0 errors",
    ),
    QueryTestCase(
        id="null_position_1",
        filter={"$and": [{"a": 1}, None]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with null at position 1 errors",
    ),
    QueryTestCase(
        id="string_position_0",
        filter={"$and": ["x", {"a": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with string at position 0 errors",
    ),
    QueryTestCase(
        id="array_position_1",
        filter={"$and": [{"a": 1}, [1, 2]]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with array at position 1 errors",
    ),
    QueryTestCase(
        id="all_non_objects",
        filter={"$and": [1, 2, 3]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with all non-object elements errors",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_and_errors(collection, test):
    """Test $and with invalid arguments returns correct error code."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
