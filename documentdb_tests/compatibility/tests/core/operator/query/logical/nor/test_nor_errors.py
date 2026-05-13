"""
Tests for $nor query operator error handling.

Covers invalid argument types, invalid array element types,
empty array, non-top-level usage, and invalid operators inside expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}]

INVALID_ARGUMENT_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="non_array_object",
        filter={"$nor": {"price": 1.99}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with non-array object argument should return BadValue error",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"$nor": None},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with null argument should return BadValue error",
    ),
    QueryTestCase(
        id="string_argument",
        filter={"$nor": "invalid"},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with string argument should return BadValue error",
    ),
    QueryTestCase(
        id="numeric_argument",
        filter={"$nor": 123},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with numeric argument should return BadValue error",
    ),
    QueryTestCase(
        id="boolean_argument",
        filter={"$nor": True},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with boolean argument should return BadValue error",
    ),
]

INVALID_ELEMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="non_object_element_integer",
        filter={"$nor": [123]},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with integer element in array should return BadValue error",
    ),
    QueryTestCase(
        id="non_object_element_string",
        filter={"$nor": ["invalid"]},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with string element in array should return BadValue error",
    ),
    QueryTestCase(
        id="non_object_element_null",
        filter={"$nor": [None]},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with null element in array should return BadValue error",
    ),
    QueryTestCase(
        id="non_object_element_array",
        filter={"$nor": [[{"a": 1}]]},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with array element in array should return BadValue error",
    ),
]

EMPTY_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array",
        filter={"$nor": []},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with empty array should return BadValue error",
    ),
]

ERROR_HANDLING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="non_top_level_position",
        filter={"field": {"$nor": [{"a": 1}]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor at non-top-level position should return BadValue error",
    ),
    QueryTestCase(
        id="invalid_operator_inside_expression",
        filter={"$nor": [{"val": {"$invalid": 1}}]},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with invalid operator inside expression should return BadValue error",
    ),
    QueryTestCase(
        id="mixed_valid_invalid_expressions",
        filter={"$nor": [{"a": 1}, {"val": {"$invalid": 1}}]},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$nor with mixed valid/invalid expressions should return BadValue error",
    ),
]

ALL_TESTS = (
    INVALID_ARGUMENT_TYPE_TESTS + INVALID_ELEMENT_TESTS + EMPTY_ARRAY_TESTS + ERROR_HANDLING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_errors(collection, test):
    """Test $nor query operator error handling."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
    )
