"""
Tests for $or edge cases.

Tests empty collection, no-match, single-document, null/missing field handling,
$exists behavior, and nested $or nesting.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="no_clause_matches",
        filter={"$or": [{"a": 99}, {"b": 99}]},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 3}],
        expected=[],
        msg="$or where no clause matches returns empty",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"$or": [{"a": 1}, {"b": 2}]},
        doc=[],
        expected=[],
        msg="$or on empty collection returns empty",
    ),
    QueryTestCase(
        id="single_document_match",
        filter={"$or": [{"a": 1}, {"b": 99}]},
        doc=[{"_id": 1, "a": 1, "b": 2}],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="$or on single-document collection matches correctly",
    ),
    QueryTestCase(
        id="single_document_no_match",
        filter={"$or": [{"a": 99}, {"b": 99}]},
        doc=[{"_id": 1, "a": 1, "b": 2}],
        expected=[],
        msg="$or on single-document collection returns empty when not matched",
    ),
    QueryTestCase(
        id="null_field_matches",
        filter={"$or": [{"a": None}, {"b": 1}]},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "b": 1}, {"_id": 3, "a": 1}],
        expected=[{"_id": 1, "a": None}, {"_id": 2, "b": 1}],
        msg="$or with null clause matches null field",
    ),
    QueryTestCase(
        id="exists_true_matches",
        filter={"$or": [{"a": {"$exists": True}}, {"b": 1}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "b": 1}, {"_id": 3, "c": 1}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "b": 1}],
        msg="$or with $exists:true matches docs with field present",
    ),
    QueryTestCase(
        id="exists_true_no_match",
        filter={"$or": [{"a": {"$exists": True}}, {"b": 1}]},
        doc=[{"_id": 1, "c": 1}],
        expected=[],
        msg="$or with $exists:true does not match when no clause satisfied",
    ),
    QueryTestCase(
        id="nested_or",
        filter={"$or": [{"$or": [{"a": 1}, {"b": 2}]}, {"c": 3}]},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "c": 3},
            {"_id": 4, "d": 4},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "b": 2}, {"_id": 3, "c": 3}],
        msg="Nested $or matches documents satisfying any inner or outer clause",
    ),
    QueryTestCase(
        id="clause_ordering_invariance",
        filter={"$or": [{"b": 2}, {"a": 1}]},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "c": 3},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "b": 2}],
        msg="$or with reversed clause order produces same results",
    ),
    QueryTestCase(
        id="top_level_filter_implicit_and",
        filter={"x": 1, "$or": [{"a": 1}, {"b": 2}]},
        doc=[
            {"_id": 1, "x": 1, "a": 1},
            {"_id": 2, "x": 1, "b": 2},
            {"_id": 3, "x": 2, "a": 1},
            {"_id": 4, "x": 1, "c": 3},
        ],
        expected=[{"_id": 1, "x": 1, "a": 1}, {"_id": 2, "x": 1, "b": 2}],
        msg="$or combined with top-level field acts as implicit AND",
    ),
    QueryTestCase(
        id="empty_string_field_name",
        filter={"$or": [{"": 1}]},
        doc=[{"_id": 1, "": 1}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "": 1}],
        msg="$or with empty string field name matches doc with empty key",
    ),
    QueryTestCase(
        id="three_level_nesting",
        filter={"$or": [{"$or": [{"$or": [{"a": 1}]}, {"b": 2}]}, {"c": 3}]},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "c": 3},
            {"_id": 4, "d": 4},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "b": 2}, {"_id": 3, "c": 3}],
        msg="Three-level nested $or matches correctly",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_or_edge_cases(collection, test):
    """Test $or edge cases."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
