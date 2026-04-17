"""
Tests for $gt field lookup and array value comparison.

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
        filter={"a": {"$gt": 10}},
        doc=[{"_id": 1, "a": [3, 7, 12]}, {"_id": 2, "a": [1, 5]}],
        expected=[{"_id": 1, "a": [3, 7, 12]}],
        msg="$gt matches if any array element satisfies condition",
    ),
    QueryTestCase(
        id="array_no_element_match",
        filter={"a": {"$gt": 15}},
        doc=[{"_id": 1, "a": [1, 5]}],
        expected=[],
        msg="$gt on array with no element greater than query",
    ),
    QueryTestCase(
        id="array_index_zero",
        filter={"arr.0": {"$gt": 20}},
        doc=[{"_id": 1, "arr": [25, 5]}, {"_id": 2, "arr": [10, 30]}],
        expected=[{"_id": 1, "arr": [25, 5]}],
        msg="$gt on array index 0",
    ),
    QueryTestCase(
        id="numeric_key_on_object",
        filter={"a.0.b": {"$gt": 5}},
        doc=[{"_id": 1, "a": {"0": {"b": 10}}}, {"_id": 2, "a": {"0": {"b": 3}}}],
        expected=[{"_id": 1, "a": {"0": {"b": 10}}}],
        msg="$gt with numeric key on object (not array)",
    ),
    QueryTestCase(
        id="id_objectid",
        filter={"_id": {"$gt": ObjectId("507f1f77bcf86cd799439012")}},
        doc=[
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "a": 1},
            {"_id": ObjectId("507f1f77bcf86cd799439013"), "a": 2},
        ],
        expected=[{"_id": ObjectId("507f1f77bcf86cd799439013"), "a": 2}],
        msg="$gt on _id with ObjectId",
    ),
    QueryTestCase(
        id="array_of_embedded_docs_dot_notation",
        filter={"a.b": {"$gt": 10}},
        doc=[
            {"_id": 1, "a": [{"b": 3}, {"b": 15}]},
            {"_id": 2, "a": [{"b": 1}, {"b": 5}]},
        ],
        expected=[{"_id": 1, "a": [{"b": 3}, {"b": 15}]}],
        msg="$gt on array of embedded docs via dot notation",
    ),
    QueryTestCase(
        id="nested_array_double_index",
        filter={"a.0.0": {"$gt": 5}},
        doc=[{"_id": 1, "a": [[10, 2], [3, 4]]}, {"_id": 2, "a": [[1, 2], [3, 4]]}],
        expected=[{"_id": 1, "a": [[10, 2], [3, 4]]}],
        msg="$gt on a.0.0 resolves nested array index to first element of first sub-array",
    ),
]

ARRAY_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_gt_array_element_comparison",
        filter={"a": {"$gt": [1, 2]}},
        doc=[{"_id": 1, "a": [1, 3]}],
        expected=[{"_id": 1, "a": [1, 3]}],
        msg="$gt array [1,3] > [1,2] via array comparison",
    ),
    QueryTestCase(
        id="longer_array_gt_shorter_prefix",
        filter={"a": {"$gt": [1, 2]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$gt longer array is greater than shorter prefix",
    ),
    QueryTestCase(
        id="nonempty_array_gt_empty_array",
        filter={"a": {"$gt": []}},
        doc=[{"_id": 1, "a": [1]}],
        expected=[{"_id": 1, "a": [1]}],
        msg="$gt non-empty array is greater than empty array",
    ),
    QueryTestCase(
        id="array_with_null_element_gt_scalar",
        filter={"a": {"$gt": 3}},
        doc=[{"_id": 1, "a": [None, 5]}],
        expected=[{"_id": 1, "a": [None, 5]}],
        msg="$gt matches array with element 5 > 3",
    ),
    QueryTestCase(
        id="equal_array_not_gt",
        filter={"a": {"$gt": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[],
        msg="equal array [1,2,3] does not match $gt [1,2,3]",
    ),
    QueryTestCase(
        id="empty_array_not_gt_scalar",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="$gt empty array does not match scalar query",
    ),
]

ALL_TESTS = FIELD_LOOKUP_TESTS + ARRAY_VALUE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gt_field_lookup(collection, test):
    """Parametrized test for $gt field lookup and array comparison."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
