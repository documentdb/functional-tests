"""
Tests for $exists edge cases and null/missing field distinction.

Covers null vs missing field semantics, empty collection, all/no documents
having the field, and falsy values (zero, false, empty string, empty array,
empty object) do NOT match $exists: false.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="true_mixed_presence",
        filter={"a": {"$exists": True}},
        doc=[
            {"_id": 1, "a": None, "b": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "a": 1, "b": 3},
            {"_id": 4, "a": False, "b": 4},
        ],
        expected=[
            {"_id": 1, "a": None, "b": 1},
            {"_id": 3, "a": 1, "b": 3},
            {"_id": 4, "a": False, "b": 4},
        ],
        msg="$exists: true returns all docs with field a (including null and false)",
    ),
    QueryTestCase(
        id="false_mixed_presence",
        filter={"a": {"$exists": False}},
        doc=[
            {"_id": 1, "a": None, "b": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "a": 1, "b": 3},
            {"_id": 4, "a": False, "b": 4},
        ],
        expected=[{"_id": 2, "b": 2}],
        msg="$exists: false returns only doc without field a",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_collection_true",
        filter={"a": {"$exists": True}},
        doc=[],
        expected=[],
        msg="$exists: true on empty collection returns nothing",
    ),
    QueryTestCase(
        id="empty_collection_false",
        filter={"a": {"$exists": False}},
        doc=[],
        expected=[],
        msg="$exists: false on empty collection returns nothing",
    ),
    QueryTestCase(
        id="all_have_field",
        filter={"a": {"$exists": False}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[],
        msg="$exists: false returns nothing when all docs have field",
    ),
    QueryTestCase(
        id="none_have_field",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "b": 1}, {"_id": 2, "b": 2}],
        expected=[],
        msg="$exists: true returns nothing when no docs have field",
    ),
    QueryTestCase(
        id="zero_not_false",
        filter={"a": {"$exists": False}},
        doc=[{"_id": 1, "a": 0}],
        expected=[],
        msg="Zero value does NOT match $exists: false",
    ),
    QueryTestCase(
        id="false_value_not_false",
        filter={"a": {"$exists": False}},
        doc=[{"_id": 1, "a": False}],
        expected=[],
        msg="False value does NOT match $exists: false",
    ),
    QueryTestCase(
        id="empty_string_not_false",
        filter={"a": {"$exists": False}},
        doc=[{"_id": 1, "a": ""}],
        expected=[],
        msg="Empty string does NOT match $exists: false",
    ),
    QueryTestCase(
        id="empty_array_not_false",
        filter={"a": {"$exists": False}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="Empty array does NOT match $exists: false",
    ),
    QueryTestCase(
        id="empty_object_not_false",
        filter={"a": {"$exists": False}},
        doc=[{"_id": 1, "a": {}}],
        expected=[],
        msg="Empty object does NOT match $exists: false",
    ),
]

ALL_TESTS = NULL_MISSING_TESTS + EDGE_CASE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_exists_edge_cases(collection, test):
    """Parametrized test for $exists edge cases and null/missing distinction."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
