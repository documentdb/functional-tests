"""
Tests for $all query operator argument handling.

Validates valid arguments and empty array behavior.

"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

VALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="single_element",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": ["x", "y"]}, {"_id": 2, "a": ["y"]}],
        expected=[{"_id": 1, "a": ["x", "y"]}],
        msg="Single element $all should match docs containing that element",
    ),
    QueryTestCase(
        id="many_elements",
        filter={"a": {"$all": ["a", "b", "c", "d", "e"]}},
        doc=[{"_id": 1, "a": ["a", "b", "c", "d", "e"]}, {"_id": 2, "a": ["a", "b", "c"]}],
        expected=[{"_id": 1, "a": ["a", "b", "c", "d", "e"]}],
        msg="Many elements $all should require all present",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_ARGUMENT_TESTS))
def test_all_valid_arguments(collection, test):
    """Test $all with valid array arguments."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


EMPTY_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="populated_collection",
        filter={"a": {"$all": []}},
        doc=[{"_id": 1, "a": ["x"]}, {"_id": 2, "a": []}],
        expected=[],
        msg="$all with empty array should match no documents in populated collection",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"a": {"$all": []}},
        doc=[],
        expected=[],
        msg="$all with empty array should match no documents in empty collection",
    ),
    QueryTestCase(
        id="in_or",
        filter={"$or": [{"a": {"$all": []}}]},
        doc=[{"_id": 1, "a": ["x"]}, {"_id": 2, "a": ["y"]}],
        expected=[],
        msg="$all with empty array in $or should return no results (always false)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMPTY_ARRAY_TESTS))
def test_all_empty_array(collection, test):
    """Test $all with empty array as always-false."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)
