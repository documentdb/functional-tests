"""
Tests for $in query operator argument handling.

Covers empty array, single element, many elements, duplicates, mixed types,
dollar-prefixed string literals, large arrays, equivalence to $or,
and invalid (non-array) arguments.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SUCCESS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array_no_results",
        filter={"x": {"$in": []}},
        doc=[{"_id": 1, "x": 1}],
        expected=[],
        msg="$in with empty array returns nothing",
    ),
    QueryTestCase(
        id="single_element_equality",
        filter={"x": {"$in": [1]}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        expected=[{"_id": 1, "x": 1}],
        msg="$in with single element array is equivalent to equality",
    ),
    QueryTestCase(
        id="many_elements_match_any",
        filter={"x": {"$in": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}},
        doc=[{"_id": i, "x": i} for i in range(1, 11)],
        expected=[{"_id": i, "x": i} for i in range(1, 11)],
        msg="$in with many elements matches any",
    ),
    QueryTestCase(
        id="duplicate_values_in_array",
        filter={"x": {"$in": [1, 1, 1]}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        expected=[{"_id": 1, "x": 1}],
        msg="$in with duplicate values in array matches docs where x is 1",
    ),
    QueryTestCase(
        id="mixed_types_in_array",
        filter={"x": {"$in": [1, "hello", True, None]}},
        doc=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": "hello"},
            {"_id": 3, "x": True},
            {"_id": 4, "x": None},
            {"_id": 5, "x": 99},
        ],
        expected=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": "hello"},
            {"_id": 3, "x": True},
            {"_id": 4, "x": None},
        ],
        msg="$in with mixed types in array matches docs where x is any of those values",
    ),
    QueryTestCase(
        id="dollar_prefixed_string_as_literal",
        filter={"x": {"$in": ["$abc"]}},
        doc=[{"_id": 1, "x": "$abc"}, {"_id": 2, "x": "abc"}],
        expected=[{"_id": 1, "x": "$abc"}],
        msg="$in treats dollar-prefixed string as literal value, not operator",
    ),
    QueryTestCase(
        id="large_array_100_elements",
        filter={"x": {"$in": list(range(100))}},
        doc=[{"_id": 1, "x": 50}, {"_id": 2, "x": 200}],
        expected=[{"_id": 1, "x": 50}],
        msg="$in with 100 elements matches correctly",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUCCESS_TESTS))
def test_in_argument_handling(collection, test_case):
    """Parametrized test for $in valid argument handling."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)


ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="non_array_int",
        filter={"x": {"$in": 1}},
        doc=[{"_id": 1, "x": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$in with non-array int argument returns error",
    ),
    QueryTestCase(
        id="non_array_string",
        filter={"x": {"$in": "hello"}},
        doc=[{"_id": 1, "x": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$in with non-array string argument returns error",
    ),
    QueryTestCase(
        id="non_array_object",
        filter={"x": {"$in": {"a": 1}}},
        doc=[{"_id": 1, "x": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$in with non-array object argument returns error",
    ),
    QueryTestCase(
        id="non_array_null",
        filter={"x": {"$in": None}},
        doc=[{"_id": 1, "x": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$in with non-array null argument returns error",
    ),
    QueryTestCase(
        id="non_array_boolean",
        filter={"x": {"$in": True}},
        doc=[{"_id": 1, "x": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$in with non-array boolean argument returns error",
    ),
    QueryTestCase(
        id="query_operator_in_array",
        filter={"x": {"$in": [{"$gt": 1}]}},
        doc=[{"_id": 1, "x": 2}],
        error_code=BAD_VALUE_ERROR,
        msg="$in with query operator object in array returns error",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ERROR_TESTS))
def test_in_argument_handling_errors(collection, test_case):
    """Parametrized test for $in invalid argument handling."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertFailureCode(result, test_case.error_code, test_case.msg)
