"""
Tests for $and edge cases.

Tests empty collection, all-match, no-match, single-document, and $exists behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "a": 1, "b": 2},
    {"_id": 2, "a": 2, "b": 3},
    {"_id": 3, "a": 3, "b": 4},
]

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="all_clauses_match_all",
        filter={"$and": [{"a": {"$gte": 1}}, {"b": {"$gte": 2}}]},
        doc=DOCS,
        expected=DOCS,
        msg="$and where all clauses match all documents returns all",
    ),
    QueryTestCase(
        id="no_clause_matches",
        filter={"$and": [{"a": 99}, {"b": 99}]},
        doc=DOCS,
        expected=[],
        msg="$and where no clause matches returns empty",
    ),
    QueryTestCase(
        id="single_document_match",
        filter={"$and": [{"a": 1}, {"b": 2}]},
        doc=[{"_id": 1, "a": 1, "b": 2}],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="$and on single-document collection matches correctly",
    ),
    QueryTestCase(
        id="single_document_no_match",
        filter={"$and": [{"a": 1}, {"b": 99}]},
        doc=[{"_id": 1, "a": 1, "b": 2}],
        expected=[],
        msg="$and on single-document collection returns empty when not matched",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"$and": [{"a": 1}, {"b": 2}]},
        doc=[],
        expected=[],
        msg="$and on empty collection returns empty",
    ),
    QueryTestCase(
        id="exists_true_matches",
        filter={"$and": [{"a": {"$exists": True}}, {"b": 1}]},
        doc=[{"_id": 1, "a": 1, "b": 1}, {"_id": 2, "b": 1}],
        expected=[{"_id": 1, "a": 1, "b": 1}],
        msg="$and with $exists:true matches only docs with field present",
    ),
    QueryTestCase(
        id="exists_true_no_match_missing",
        filter={"$and": [{"a": {"$exists": True}}, {"b": 1}]},
        doc=[{"_id": 1, "b": 1}],
        expected=[],
        msg="$and with $exists:true does not match missing field",
    ),
    QueryTestCase(
        id="exists_false_matches_missing",
        filter={"$and": [{"a": {"$exists": False}}, {"b": 1}]},
        doc=[{"_id": 1, "b": 1}, {"_id": 2, "a": 1, "b": 1}],
        expected=[{"_id": 1, "b": 1}],
        msg="$and with $exists:false matches docs without the field",
    ),
    QueryTestCase(
        id="exists_false_no_match_present",
        filter={"$and": [{"a": {"$exists": False}}, {"b": 1}]},
        doc=[{"_id": 1, "a": 1, "b": 1}],
        expected=[],
        msg="$and with $exists:false does not match docs with field present",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_edge_cases(collection, test):
    """Test $and edge cases."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
