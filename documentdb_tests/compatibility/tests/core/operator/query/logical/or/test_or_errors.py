"""
Tests for $or error cases and invalid argument handling.

Tests that $or returns correct error codes for malformed expressions,
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
        filter={"$or": []},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with empty array errors",
    ),
    QueryTestCase(
        id="not_array_object",
        filter={"$or": {"a": 1}},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with object instead of array errors",
    ),
    QueryTestCase(
        id="not_array_int",
        filter={"$or": 1},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with integer errors",
    ),
    QueryTestCase(
        id="not_array_string",
        filter={"$or": "string"},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with string errors",
    ),
    QueryTestCase(
        id="not_array_null",
        filter={"$or": None},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with null errors",
    ),
    QueryTestCase(
        id="element_int",
        filter={"$or": [1]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with integer element errors",
    ),
    QueryTestCase(
        id="element_string",
        filter={"$or": ["string"]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with string element errors",
    ),
    QueryTestCase(
        id="element_null",
        filter={"$or": [None]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with null element errors",
    ),
    QueryTestCase(
        id="element_bool",
        filter={"$or": [True]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with boolean element errors",
    ),
    QueryTestCase(
        id="non_object_position_0",
        filter={"$or": [1, {"a": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with non-object at position 0 errors",
    ),
    QueryTestCase(
        id="non_object_position_1",
        filter={"$or": [{"a": 1}, 1]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with non-object at position 1 errors",
    ),
    QueryTestCase(
        id="non_object_position_2",
        filter={"$or": [{"a": 1}, {"b": 2}, 1]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with non-object at position 2 errors",
    ),
    QueryTestCase(
        id="null_position_0",
        filter={"$or": [None, {"a": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with null at position 0 errors",
    ),
    QueryTestCase(
        id="null_position_1",
        filter={"$or": [{"a": 1}, None]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with null at position 1 errors",
    ),
    QueryTestCase(
        id="string_position_0",
        filter={"$or": ["x", {"a": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with string at position 0 errors",
    ),
    QueryTestCase(
        id="array_position_1",
        filter={"$or": [{"a": 1}, [1, 2]]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with array at position 1 errors",
    ),
    QueryTestCase(
        id="all_non_objects",
        filter={"$or": [1, 2, 3]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with all non-object elements errors",
    ),
    QueryTestCase(
        id="unknown_operator",
        filter={"$or": [{"$invalidOp": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$or with unknown query operator errors",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_or_errors(collection, test):
    """Test $or with invalid arguments returns correct error code."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
