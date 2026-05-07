"""
Tests for $or argument handling.

Tests argument count variations, valid argument patterns, and deduplication
behavior when multiple clauses match the same document.
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
        filter={"$or": [{"a": 1}]},
        doc=DOCS,
        expected=[
            {"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
            {"_id": 3, "a": 1, "b": 3, "c": 3, "d": 4, "e": 5},
        ],
        msg="$or with single expression matches documents satisfying it",
    ),
    QueryTestCase(
        id="two_expressions",
        filter={"$or": [{"a": 1}, {"a": 2}]},
        doc=DOCS,
        expected=DOCS,
        msg="$or with two expressions matches documents satisfying either",
    ),
    QueryTestCase(
        id="five_expressions",
        filter={"$or": [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}, {"e": 5}]},
        doc=DOCS,
        expected=DOCS,
        msg="$or with five expressions matches documents satisfying any",
    ),
    QueryTestCase(
        id="empty_object_expression",
        filter={"$or": [{}]},
        doc=DOCS,
        expected=DOCS,
        msg="$or with empty object matches all documents",
    ),
    QueryTestCase(
        id="duplicate_same_field_same_value",
        filter={"$or": [{"a": 1}, {"a": 1}, {"a": 1}]},
        doc=DOCS,
        expected=[
            {"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
            {"_id": 3, "a": 1, "b": 3, "c": 3, "d": 4, "e": 5},
        ],
        msg="$or with repeated identical clauses does not duplicate results",
    ),
    QueryTestCase(
        id="mutually_exclusive",
        filter={"$or": [{"a": 1}, {"a": 2}]},
        doc=DOCS,
        expected=DOCS,
        msg="$or with mutually exclusive clauses matches union",
    ),
    QueryTestCase(
        id="large_array_100_expressions",
        filter={"$or": [{"a": 1}] * 100},
        doc=DOCS,
        expected=[
            {"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
            {"_id": 3, "a": 1, "b": 3, "c": 3, "d": 4, "e": 5},
        ],
        msg="$or with 100 expressions does not hit a limit",
    ),
    QueryTestCase(
        id="dedup_overlapping_clauses",
        filter={"$or": [{"a": {"$gt": 0}}, {"a": {"$lt": 10}}]},
        doc=[{"_id": 1, "a": 5}],
        expected=[{"_id": 1, "a": 5}],
        msg="$or does not return duplicates when multiple clauses match same doc",
    ),
    QueryTestCase(
        id="dedup_all_match_all",
        filter={"$or": [{"a": {"$gte": 1}}, {"b": {"$gte": 2}}]},
        doc=DOCS,
        expected=DOCS,
        msg="$or where all clauses match all documents returns all without duplicates",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_or_argument_success(collection, test):
    """Test $or with valid argument variations."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
