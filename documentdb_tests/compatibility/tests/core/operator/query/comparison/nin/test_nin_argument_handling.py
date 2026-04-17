"""
Tests for $nin argument handling.

Covers valid array argument variations, invalid argument formats,
duplicate values, empty arrays, and large arrays.
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
        id="empty_array_matches_all",
        filter={"a": {"$nin": []}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        msg="$nin with empty array matches ALL documents",
    ),
    QueryTestCase(
        id="single_element",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 2, "a": 2}],
        msg="$nin with single element array",
    ),
    QueryTestCase(
        id="two_elements",
        filter={"a": {"$nin": [1, 2]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        expected=[{"_id": 3, "a": 3}],
        msg="$nin with two element array",
    ),
    QueryTestCase(
        id="duplicate_values_same_as_single",
        filter={"a": {"$nin": [1, 1, 1]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 2, "a": 2}],
        msg="$nin with duplicate values behaves same as single value",
    ),
    QueryTestCase(
        id="large_array_1000_elements",
        filter={"a": {"$nin": list(range(1000))}},
        doc=[{"_id": 1, "a": 9999}, {"_id": 2, "a": 500}],
        expected=[{"_id": 1, "a": 9999}],
        msg="$nin with 1000 elements in array",
    ),
    QueryTestCase(
        id="many_elements_excludes_range",
        filter={"a": {"$nin": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}},
        doc=[{"_id": i, "a": i} for i in range(1, 12)],
        expected=[{"_id": 11, "a": 11}],
        msg="$nin with many elements excludes all matching values",
    ),
    QueryTestCase(
        id="mixed_types_in_array",
        filter={"a": {"$nin": [1, "hello", True, None]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": "hello"},
            {"_id": 3, "a": True},
            {"_id": 4, "a": None},
            {"_id": 5, "a": 99},
        ],
        expected=[{"_id": 5, "a": 99}],
        msg="$nin with mixed types in array excludes all matching docs",
    ),
    QueryTestCase(
        id="dollar_prefixed_string_as_literal",
        filter={"a": {"$nin": ["$abc"]}},
        doc=[{"_id": 1, "a": "$abc"}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$nin treats dollar-prefixed string as literal value, not operator",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUCCESS_TESTS))
def test_nin_argument_handling(collection, test_case):
    """Parametrized test for $nin valid argument handling."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, ignore_doc_order=True)


ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="integer_argument_errors",
        filter={"a": {"$nin": 1}},
        doc=[{"_id": 1, "a": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$nin with integer argument returns error code 2",
    ),
    QueryTestCase(
        id="string_argument_errors",
        filter={"a": {"$nin": "string"}},
        doc=[{"_id": 1, "a": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$nin with string argument returns error code 2",
    ),
    QueryTestCase(
        id="boolean_argument_errors",
        filter={"a": {"$nin": True}},
        doc=[{"_id": 1, "a": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$nin with boolean argument returns error code 2",
    ),
    QueryTestCase(
        id="null_argument_errors",
        filter={"a": {"$nin": None}},
        doc=[{"_id": 1, "a": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$nin with null argument returns error code 2",
    ),
    QueryTestCase(
        id="object_argument_errors",
        filter={"a": {"$nin": {"a": 1}}},
        doc=[{"_id": 1, "a": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$nin with object argument returns error code 2",
    ),
    QueryTestCase(
        id="query_operator_in_array_errors",
        filter={"a": {"$nin": [{"$gt": 1}]}},
        doc=[{"_id": 1, "a": 1}],
        error_code=BAD_VALUE_ERROR,
        msg="$nin with query operator object in array returns error code 2",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ERROR_TESTS))
def test_nin_argument_handling_errors(collection, test_case):
    """Parametrized test for $nin invalid argument handling."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertFailureCode(result, test_case.error_code)
