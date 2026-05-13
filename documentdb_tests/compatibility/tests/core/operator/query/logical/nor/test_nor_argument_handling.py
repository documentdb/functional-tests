"""
Tests for $nor query operator argument handling.

Covers array argument validation, expression element validation,
and error cases for invalid argument types.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}]

INVALID_ARGUMENT_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="non_array_object",
        filter={"$nor": {"price": 1.99}},
        doc=DOCS,
        error_code=2,
        msg="$nor with non-array object argument should return BadValue error",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"$nor": None},
        doc=DOCS,
        error_code=2,
        msg="$nor with null argument should return BadValue error",
    ),
    QueryTestCase(
        id="string_argument",
        filter={"$nor": "invalid"},
        doc=DOCS,
        error_code=2,
        msg="$nor with string argument should return BadValue error",
    ),
    QueryTestCase(
        id="numeric_argument",
        filter={"$nor": 123},
        doc=DOCS,
        error_code=2,
        msg="$nor with numeric argument should return BadValue error",
    ),
    QueryTestCase(
        id="boolean_argument",
        filter={"$nor": True},
        doc=DOCS,
        error_code=2,
        msg="$nor with boolean argument should return BadValue error",
    ),
]

INVALID_ELEMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="non_object_element_integer",
        filter={"$nor": [123]},
        doc=DOCS,
        error_code=2,
        msg="$nor with integer element in array should return BadValue error",
    ),
    QueryTestCase(
        id="non_object_element_string",
        filter={"$nor": ["invalid"]},
        doc=DOCS,
        error_code=2,
        msg="$nor with string element in array should return BadValue error",
    ),
    QueryTestCase(
        id="non_object_element_null",
        filter={"$nor": [None]},
        doc=DOCS,
        error_code=2,
        msg="$nor with null element in array should return BadValue error",
    ),
    QueryTestCase(
        id="non_object_element_array",
        filter={"$nor": [[{"a": 1}]]},
        doc=DOCS,
        error_code=2,
        msg="$nor with array element in array should return BadValue error",
    ),
]

VALID_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array",
        filter={"$nor": []},
        doc=DOCS,
        error_code=2,
        msg="$nor with empty array should return BadValue error",
    ),
    QueryTestCase(
        id="single_expression",
        filter={"$nor": [{"a": 1}]},
        doc=DOCS,
        expected=[{"_id": 2, "a": 2, "b": 1}],
        msg="$nor with single expression should exclude matching docs",
    ),
    QueryTestCase(
        id="two_expressions",
        filter={"$nor": [{"a": 1}, {"b": 1}]},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}, {"_id": 3, "a": 2, "b": 2}],
        expected=[{"_id": 3, "a": 2, "b": 2}],
        msg="$nor with two expressions should return docs failing both",
    ),
    QueryTestCase(
        id="many_expressions",
        filter={"$nor": [{"a": 1}, {"b": 1}, {"a": 3}, {"b": 3}, {"a": 4}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2, "b": 2}],
        expected=[{"_id": 2, "a": 2, "b": 2}],
        msg="$nor with many expressions should return docs failing all",
    ),
    QueryTestCase(
        id="empty_object_in_array",
        filter={"$nor": [{}]},
        doc=DOCS,
        expected=[],
        msg="$nor with empty object matches all docs so returns empty",
    ),
]

ERROR_HANDLING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="non_top_level_position",
        filter={"field": {"$nor": [{"a": 1}]}},
        doc=DOCS,
        error_code=2,
        msg="$nor at non-top-level position should return BadValue error",
    ),
    QueryTestCase(
        id="invalid_operator_inside_expression",
        filter={"$nor": [{"val": {"$invalid": 1}}]},
        doc=DOCS,
        error_code=2,
        msg="$nor with invalid operator inside expression should return BadValue error",
    ),
    QueryTestCase(
        id="mixed_valid_invalid_expressions",
        filter={"$nor": [{"a": 1}, {"val": {"$invalid": 1}}]},
        doc=DOCS,
        error_code=2,
        msg="$nor with mixed valid/invalid expressions should return BadValue error",
    ),
]

ALL_TESTS = (
    INVALID_ARGUMENT_TYPE_TESTS + INVALID_ELEMENT_TESTS + VALID_ARRAY_TESTS + ERROR_HANDLING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_argument_handling(collection, test):
    """Test $nor query operator argument validation."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
