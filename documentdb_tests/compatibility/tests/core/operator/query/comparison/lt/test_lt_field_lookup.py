"""
Tests for $lt field lookup and array value comparison.

Covers array element matching, array index access,
numeric key disambiguation, _id with ObjectId, array of embedded documents,
whole-array comparison, empty array behavior, and embedded document dot-notation.
"""

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

FIELD_LOOKUP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_element_matching",
        filter={"a": {"$lt": 5}},
        doc=[{"_id": 1, "a": [3, 7, 12]}, {"_id": 2, "a": [10, 20]}],
        expected=[{"_id": 1, "a": [3, 7, 12]}],
        msg="$lt matches if any array element satisfies condition",
    ),
    QueryTestCase(
        id="array_no_element_match",
        filter={"a": {"$lt": 5}},
        doc=[{"_id": 1, "a": [10, 20]}],
        expected=[],
        msg="$lt on array with no element less than query",
    ),
    QueryTestCase(
        id="array_index_zero",
        filter={"arr.0": {"$lt": 20}},
        doc=[{"_id": 1, "arr": [10, 30]}, {"_id": 2, "arr": [25, 5]}],
        expected=[{"_id": 1, "arr": [10, 30]}],
        msg="$lt on array index 0",
    ),
    QueryTestCase(
        id="numeric_key_on_object",
        filter={"a.0.b": {"$lt": 5}},
        doc=[{"_id": 1, "a": {"0": {"b": 3}}}, {"_id": 2, "a": {"0": {"b": 10}}}],
        expected=[{"_id": 1, "a": {"0": {"b": 3}}}],
        msg="$lt with numeric key on object (not array)",
    ),
    QueryTestCase(
        id="id_objectid",
        filter={"_id": {"$lt": ObjectId("507f1f77bcf86cd799439012")}},
        doc=[
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "a": 1},
            {"_id": ObjectId("507f1f77bcf86cd799439013"), "a": 2},
        ],
        expected=[{"_id": ObjectId("507f1f77bcf86cd799439011"), "a": 1}],
        msg="$lt on _id with ObjectId",
    ),
    QueryTestCase(
        id="array_of_embedded_docs_dot_notation",
        filter={"a.b": {"$lt": 5}},
        doc=[
            {"_id": 1, "a": [{"b": 3}, {"b": 7}]},
            {"_id": 2, "a": [{"b": 10}, {"b": 20}]},
        ],
        expected=[{"_id": 1, "a": [{"b": 3}, {"b": 7}]}],
        msg="$lt on array of embedded docs via dot notation",
    ),
]

ARRAY_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_lt_array_element_comparison",
        filter={"a": {"$lt": [1, 3]}},
        doc=[{"_id": 1, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$lt array [1,2] < [1,3] via array comparison",
    ),
    QueryTestCase(
        id="shorter_array_prefix_lt_longer",
        filter={"a": {"$lt": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$lt shorter array prefix is less than longer",
    ),
    QueryTestCase(
        id="empty_array_lt_nonempty_array",
        filter={"a": {"$lt": [1]}},
        doc=[{"_id": 1, "a": []}],
        expected=[{"_id": 1, "a": []}],
        msg="$lt empty array is less than non-empty array",
    ),
    QueryTestCase(
        id="array_with_null_element_lt_scalar",
        filter={"a": {"$lt": 10}},
        doc=[{"_id": 1, "a": [None, 5]}],
        expected=[{"_id": 1, "a": [None, 5]}],
        msg="$lt matches array with element 5 < 10",
    ),
    QueryTestCase(
        id="empty_array_not_lt_scalar",
        filter={"a": {"$lt": 5}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="$lt empty array does not match scalar query",
    ),
]

EMBEDDED_DOC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="embedded_field_lt",
        filter={"carrier.fee": {"$lt": 4}},
        doc=[
            {"_id": 1, "item": "nuts", "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 2, "item": "bolts", "carrier": {"name": "Shipit", "fee": 4}},
            {"_id": 3, "item": "washers", "carrier": {"name": "Shipit", "fee": 1}},
        ],
        expected=[
            {"_id": 1, "item": "nuts", "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 3, "item": "washers", "carrier": {"name": "Shipit", "fee": 1}},
        ],
        msg="$lt on embedded field returns docs with fee < 4",
    ),
    QueryTestCase(
        id="embedded_field_missing_excluded",
        filter={"carrier.fee": {"$lt": 10}},
        doc=[
            {"_id": 1, "carrier": {"fee": 3}},
            {"_id": 2, "item": "no carrier"},
        ],
        expected=[{"_id": 1, "carrier": {"fee": 3}}],
        msg="$lt on embedded field excludes docs missing the embedded path",
    ),
]

ALL_TESTS = FIELD_LOOKUP_TESTS + ARRAY_VALUE_TESTS + EMBEDDED_DOC_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lt_field_lookup(collection, test):
    """Parametrized test for $lt field lookup and array comparison."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
