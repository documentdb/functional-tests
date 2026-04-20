"""
Tests for $gte field lookup and array value comparison.

Covers array element matching, array index access,
numeric key disambiguation, _id with ObjectId, array of embedded documents,
whole-array comparison, and empty array behavior.
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
        filter={"a": {"$gte": 12}},
        doc=[{"_id": 1, "a": [3, 7, 12]}, {"_id": 2, "a": [1, 5]}],
        expected=[{"_id": 1, "a": [3, 7, 12]}],
        msg="$gte matches if any array element satisfies condition (including equal)",
    ),
    QueryTestCase(
        id="array_no_element_match",
        filter={"a": {"$gte": 15}},
        doc=[{"_id": 1, "a": [1, 5]}],
        expected=[],
        msg="$gte on array with no element greater than or equal to query",
    ),
    QueryTestCase(
        id="array_index_zero",
        filter={"arr.0": {"$gte": 25}},
        doc=[{"_id": 1, "arr": [25, 5]}, {"_id": 2, "arr": [10, 30]}],
        expected=[{"_id": 1, "arr": [25, 5]}],
        msg="$gte on array index 0 matches equal value",
    ),
    QueryTestCase(
        id="numeric_key_on_object",
        filter={"a.0.b": {"$gte": 10}},
        doc=[{"_id": 1, "a": {"0": {"b": 10}}}, {"_id": 2, "a": {"0": {"b": 3}}}],
        expected=[{"_id": 1, "a": {"0": {"b": 10}}}],
        msg="$gte with numeric key on object (not array)",
    ),
    QueryTestCase(
        id="id_objectid",
        filter={"_id": {"$gte": ObjectId("507f1f77bcf86cd799439012")}},
        doc=[
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "a": 1},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "a": 2},
            {"_id": ObjectId("507f1f77bcf86cd799439013"), "a": 3},
        ],
        expected=[
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "a": 2},
            {"_id": ObjectId("507f1f77bcf86cd799439013"), "a": 3},
        ],
        msg="$gte on _id with ObjectId includes equal",
    ),
    QueryTestCase(
        id="array_of_embedded_docs_dot_notation",
        filter={"a.b": {"$gte": 15}},
        doc=[
            {"_id": 1, "a": [{"b": 3}, {"b": 15}]},
            {"_id": 2, "a": [{"b": 1}, {"b": 5}]},
        ],
        expected=[{"_id": 1, "a": [{"b": 3}, {"b": 15}]}],
        msg="$gte on array of embedded docs via dot notation matches equal",
    ),
]

ARRAY_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_gte_array_element_comparison",
        filter={"a": {"$gte": [1, 2]}},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 3]}],
        expected=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 3]}],
        msg="$gte array includes equal and greater arrays",
    ),
    QueryTestCase(
        id="longer_array_gte_shorter_prefix",
        filter={"a": {"$gte": [1, 2]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$gte longer array is greater than or equal to shorter prefix",
    ),
    QueryTestCase(
        id="empty_array_gte_empty_array",
        filter={"a": {"$gte": []}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        msg="$gte empty array matches empty and non-empty arrays",
    ),
    QueryTestCase(
        id="array_with_null_element_gte_scalar",
        filter={"a": {"$gte": 5}},
        doc=[{"_id": 1, "a": [None, 5]}],
        expected=[{"_id": 1, "a": [None, 5]}],
        msg="$gte matches array with element 5 >= 5",
    ),
    QueryTestCase(
        id="empty_array_not_gte_scalar",
        filter={"a": {"$gte": 5}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="$gte empty array does not match scalar query",
    ),
]

ALL_TESTS = FIELD_LOOKUP_TESTS + ARRAY_VALUE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gte_field_lookup(collection, test):
    """Parametrized test for $gte field lookup and array comparison."""
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, ignore_doc_order=True)
