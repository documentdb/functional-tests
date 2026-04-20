"""
Tests for $lte field lookup and array value comparison.

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
        filter={"a": {"$lte": 3}},
        doc=[{"_id": 1, "a": [3, 7, 12]}, {"_id": 2, "a": [10, 20]}],
        expected=[{"_id": 1, "a": [3, 7, 12]}],
        msg="$lte matches if any array element satisfies condition (including equal)",
    ),
    QueryTestCase(
        id="array_no_element_match",
        filter={"a": {"$lte": 2}},
        doc=[{"_id": 1, "a": [10, 20]}],
        expected=[],
        msg="$lte on array with no element less than or equal to query",
    ),
    QueryTestCase(
        id="array_index_zero",
        filter={"arr.0": {"$lte": 10}},
        doc=[{"_id": 1, "arr": [10, 30]}, {"_id": 2, "arr": [25, 5]}],
        expected=[{"_id": 1, "arr": [10, 30]}],
        msg="$lte on array index 0 matches equal value",
    ),
    QueryTestCase(
        id="numeric_key_on_object",
        filter={"a.0.b": {"$lte": 3}},
        doc=[{"_id": 1, "a": {"0": {"b": 3}}}, {"_id": 2, "a": {"0": {"b": 10}}}],
        expected=[{"_id": 1, "a": {"0": {"b": 3}}}],
        msg="$lte with numeric key on object (not array)",
    ),
    QueryTestCase(
        id="id_objectid",
        filter={"_id": {"$lte": ObjectId("507f1f77bcf86cd799439012")}},
        doc=[
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "a": 1},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "a": 2},
            {"_id": ObjectId("507f1f77bcf86cd799439013"), "a": 3},
        ],
        expected=[
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "a": 1},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "a": 2},
        ],
        msg="$lte on _id with ObjectId includes equal",
    ),
    QueryTestCase(
        id="array_of_embedded_docs_dot_notation",
        filter={"a.b": {"$lte": 3}},
        doc=[
            {"_id": 1, "a": [{"b": 3}, {"b": 7}]},
            {"_id": 2, "a": [{"b": 10}, {"b": 20}]},
        ],
        expected=[{"_id": 1, "a": [{"b": 3}, {"b": 7}]}],
        msg="$lte on array of embedded docs via dot notation matches equal",
    ),
]

ARRAY_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_lte_array_element_comparison",
        filter={"a": {"$lte": [1, 3]}},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 3]}],
        expected=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 3]}],
        msg="$lte array includes equal and lesser arrays",
    ),
    QueryTestCase(
        id="shorter_array_prefix_lte_longer",
        filter={"a": {"$lte": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$lte shorter array prefix is less than or equal to longer",
    ),
    QueryTestCase(
        id="empty_array_lte_nonempty_array",
        filter={"a": {"$lte": [1]}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        msg="$lte empty array and equal array both match",
    ),
    QueryTestCase(
        id="array_with_null_element_lte_scalar",
        filter={"a": {"$lte": 5}},
        doc=[{"_id": 1, "a": [None, 5]}],
        expected=[{"_id": 1, "a": [None, 5]}],
        msg="$lte matches array with element 5 <= 5",
    ),
    QueryTestCase(
        id="empty_array_not_lte_scalar",
        filter={"a": {"$lte": 5}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="$lte empty array does not match scalar query",
    ),
]

EMBEDDED_DOC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="embedded_field_lte",
        filter={"carrier.fee": {"$lte": 4}},
        doc=[
            {"_id": 1, "item": "nuts", "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 2, "item": "bolts", "carrier": {"name": "Shipit", "fee": 4}},
            {"_id": 3, "item": "washers", "carrier": {"name": "Shipit", "fee": 5}},
        ],
        expected=[
            {"_id": 1, "item": "nuts", "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 2, "item": "bolts", "carrier": {"name": "Shipit", "fee": 4}},
        ],
        msg="$lte on embedded field returns docs with fee <= 4",
    ),
    QueryTestCase(
        id="embedded_field_missing_excluded",
        filter={"carrier.fee": {"$lte": 10}},
        doc=[
            {"_id": 1, "carrier": {"fee": 3}},
            {"_id": 2, "item": "no carrier"},
        ],
        expected=[{"_id": 1, "carrier": {"fee": 3}}],
        msg="$lte on embedded field excludes docs missing the embedded path",
    ),
]

ALL_TESTS = FIELD_LOOKUP_TESTS + ARRAY_VALUE_TESTS + EMBEDDED_DOC_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lte_field_lookup(collection, test):
    """Parametrized test for $lte field lookup and array comparison."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
