"""
Tests for $and argument handling.

Tests argument count variations and valid argument patterns.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
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
        expected=[
            {"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
            {"_id": 3, "a": 1, "b": 3, "c": 3, "d": 4, "e": 5},
        ],
        msg="$and with single expression matches documents satisfying it",
    ),
    QueryTestCase(
        id="two_expressions",
        filter={"$and": [{"a": 1}, {"b": 2}]},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5}],
        msg="$and with two expressions matches documents satisfying both",
    ),
    QueryTestCase(
        id="five_expressions",
        filter={"$and": [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}, {"e": 5}]},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5}],
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
        expected=[
            {"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
            {"_id": 3, "a": 1, "b": 3, "c": 3, "d": 4, "e": 5},
        ],
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
        expected=[
            {"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
            {"_id": 3, "a": 1, "b": 3, "c": 3, "d": 4, "e": 5},
        ],
        msg="$and with 100 expressions does not hit a limit",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_and_argument_success(collection, test):
    """Test $and with valid argument variations."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
