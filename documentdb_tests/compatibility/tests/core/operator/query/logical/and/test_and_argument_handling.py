"""
Tests for $and argument handling and error code validation.

Tests argument count variations, invalid argument types, per-position
validation, and correct error codes for malformed $and expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
    {"_id": 2, "a": 2, "b": 2, "c": 3, "d": 4, "e": 5},
    {"_id": 3, "a": 1, "b": 3, "c": 3, "d": 4, "e": 5},
]

SUCCESS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="single_expression",
        filter={"$and": [{"a": 1}]},
        doc=DOCS,
        expected=[DOCS[0], DOCS[2]],
        msg="$and with single expression matches documents satisfying it",
    ),
    QueryTestCase(
        id="two_expressions",
        filter={"$and": [{"a": 1}, {"b": 2}]},
        doc=DOCS,
        expected=[DOCS[0]],
        msg="$and with two expressions matches documents satisfying both",
    ),
    QueryTestCase(
        id="five_expressions",
        filter={"$and": [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}, {"e": 5}]},
        doc=DOCS,
        expected=[DOCS[0]],
        msg="$and with five expressions matches documents satisfying all",
    ),
    QueryTestCase(
        id="empty_object_expression",
        filter={"$and": [{}]},
        doc=DOCS,
        expected=DOCS,
        msg="$and with empty object matches all documents",
    ),
    QueryTestCase(
        id="duplicate_same_field_same_value",
        filter={"$and": [{"a": 1}, {"a": 1}, {"a": 1}]},
        doc=DOCS,
        expected=[DOCS[0], DOCS[2]],
        msg="$and with repeated identical clauses matches same as single clause",
    ),
    QueryTestCase(
        id="contradictory_expressions",
        filter={"$and": [{"a": 1}, {"a": 2}]},
        doc=DOCS,
        expected=[],
        msg="$and with contradictory clauses matches nothing",
    ),
    QueryTestCase(
        id="large_array_100_expressions",
        filter={"$and": [{"a": 1}] * 100},
        doc=DOCS,
        expected=[DOCS[0], DOCS[2]],
        msg="$and with 100 expressions does not hit a limit",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_and_argument_success(collection, test):
    """Test $and with valid argument variations."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


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
    QueryTestCase(
        id="unknown_operator",
        filter={"$and": [{"$invalidOp": 1}]},
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="$and with unknown query operator errors",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_and_argument_errors(collection, test):
    """Test $and with invalid arguments returns correct error code."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
