"""
Tests for $in query operator array and document matching behavior.

Covers scalar matching, result set behavior, _id field queries, array element
matching, nested arrays, exact array match, sub-array match, object equality
semantics, empty array/object, dotted path traversal, and array order independence.
"""

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

OID1 = ObjectId("507f1f77bcf86cd799439011")
OID2 = ObjectId("507f1f77bcf86cd799439012")
OID3 = ObjectId("507f1f77bcf86cd799439013")

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="scalar_all_matching_docs_returned",
        filter={"x": {"$in": [1]}},
        doc=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 1},
            {"_id": 3, "x": 1},
            {"_id": 4, "x": 1},
            {"_id": 5, "x": 1},
        ],
        expected=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 1},
            {"_id": 3, "x": 1},
            {"_id": 4, "x": 1},
            {"_id": 5, "x": 1},
        ],
        msg="$in returns all matching documents, not just first",
    ),
    QueryTestCase(
        id="scalar_multiple_values_union",
        filter={"x": {"$in": [1, 3]}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}],
        expected=[{"_id": 1, "x": 1}, {"_id": 3, "x": 3}],
        msg="$in with multiple matching values returns union",
    ),
    QueryTestCase(
        id="id_objectids",
        filter={"_id": {"$in": [OID1, OID3]}},
        doc=[{"_id": OID1, "x": 1}, {"_id": OID2, "x": 2}, {"_id": OID3, "x": 3}],
        expected=[{"_id": OID1, "x": 1}, {"_id": OID3, "x": 3}],
        msg="$in on _id with ObjectIds",
    ),
    QueryTestCase(
        id="id_mixed_types",
        filter={"_id": {"$in": [1, "abc", OID1]}},
        doc=[{"_id": 1, "x": "a"}, {"_id": "abc", "x": "b"}, {"_id": OID1, "x": "c"}],
        expected=[{"_id": 1, "x": "a"}, {"_id": "abc", "x": "b"}, {"_id": OID1, "x": "c"}],
        msg="$in on _id with mixed types",
    ),
    QueryTestCase(
        id="id_single_value",
        filter={"_id": {"$in": [OID1]}},
        doc=[{"_id": OID1, "x": 1}, {"_id": OID2, "x": 2}],
        expected=[{"_id": OID1, "x": 1}],
        msg="$in on _id with single value is equivalent to equality",
    ),
    QueryTestCase(
        id="id_null",
        filter={"_id": {"$in": [None]}},
        doc=[{"_id": None, "x": 1}, {"_id": 1, "x": 2}],
        expected=[{"_id": None, "x": 1}],
        msg="$in on _id with null matches docs with null _id",
    ),
    QueryTestCase(
        id="array_empty_no_match",
        filter={"x": {"$in": [1]}},
        doc=[{"_id": 1, "x": []}],
        expected=[],
        msg="$in does NOT match empty array field",
    ),
    QueryTestCase(
        id="array_one_element_match",
        filter={"x": {"$in": [2]}},
        doc=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": [4, 5]}],
        expected=[{"_id": 1, "x": [1, 2, 3]}],
        msg="$in matches array field with one matching element",
    ),
    QueryTestCase(
        id="array_partial_overlap_matches",
        filter={"x": {"$in": [2, 4]}},
        doc=[{"_id": 1, "x": [1, 2, 3]}],
        expected=[{"_id": 1, "x": [1, 2, 3]}],
        msg="$in on array field with partial overlap still matches",
    ),
    QueryTestCase(
        id="array_no_element_match",
        filter={"x": {"$in": [4, 5]}},
        doc=[{"_id": 1, "x": [1, 2, 3]}],
        expected=[],
        msg="$in does NOT match array field with no matching elements",
    ),
    QueryTestCase(
        id="array_null_element_match",
        filter={"x": {"$in": [None]}},
        doc=[{"_id": 1, "x": [1, None, 3]}, {"_id": 2, "x": [1, 2]}],
        expected=[{"_id": 1, "x": [1, None, 3]}],
        msg="$in with null matches array containing null",
    ),
    QueryTestCase(
        id="nested_sub_array_match",
        filter={"x": {"$in": [[1, 2]]}},
        doc=[{"_id": 1, "x": [[1, 2], [3, 4]]}],
        expected=[{"_id": 1, "x": [[1, 2], [3, 4]]}],
        msg="$in with array value matches nested sub-array element",
    ),
    QueryTestCase(
        id="nested_scalar_no_match",
        filter={"x": {"$in": [1]}},
        doc=[{"_id": 1, "x": [[1, 2], [3, 4]]}],
        expected=[],
        msg="$in scalar does NOT match nested array (1 is not a top-level element)",
    ),
    QueryTestCase(
        id="mixed_scalar_and_nested_array",
        filter={"x": {"$in": [1]}},
        doc=[{"_id": 1, "x": [1, [2, 3]]}],
        expected=[{"_id": 1, "x": [1, [2, 3]]}],
        msg="$in scalar matches top-level scalar in mixed array",
    ),
    QueryTestCase(
        id="array_partial_value_no_match",
        filter={"x": {"$in": [[1]]}},
        doc=[{"_id": 1, "x": [1, 2]}],
        expected=[],
        msg="$in with partial array value does NOT match",
    ),
    QueryTestCase(
        id="array_exact_value_match",
        filter={"x": {"$in": [[1, 2]]}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": [3, 4]}],
        expected=[{"_id": 1, "x": [1, 2]}],
        msg="$in with array value matches exact array field",
    ),
    QueryTestCase(
        id="object_exact_element_match",
        filter={"x": {"$in": [{"a": 1}]}},
        doc=[{"_id": 1, "x": [{"a": 1}, {"a": 2}]}],
        expected=[{"_id": 1, "x": [{"a": 1}, {"a": 2}]}],
        msg="$in with object matches exact object element in array",
    ),
    QueryTestCase(
        id="object_key_order_no_match",
        filter={"x": {"$in": [{"b": 2, "a": 1}]}},
        doc=[{"_id": 1, "x": [{"a": 1, "b": 2}]}],
        expected=[],
        msg="$in with object different key order does NOT match (BSON key order matters)",
    ),
    QueryTestCase(
        id="object_extra_keys_no_match",
        filter={"x": {"$in": [{"a": 1}]}},
        doc=[{"_id": 1, "x": [{"a": 1, "b": 2}]}],
        expected=[],
        msg="$in with object does NOT match object with extra keys",
    ),
    QueryTestCase(
        id="empty_object_match",
        filter={"x": {"$in": [{}]}},
        doc=[{"_id": 1, "x": {}}, {"_id": 2, "x": {"a": 1}}],
        expected=[{"_id": 1, "x": {}}],
        msg="$in with empty object matches empty object",
    ),
    QueryTestCase(
        id="empty_array_value_match",
        filter={"x": {"$in": [[]]}},
        doc=[{"_id": 1, "x": []}, {"_id": 2, "x": [1]}],
        expected=[{"_id": 1, "x": []}],
        msg="$in with empty array value matches empty array field",
    ),
    QueryTestCase(
        id="object_key_order_scalar_no_match",
        filter={"x": {"$in": [{"b": 2, "a": 1}]}},
        doc=[{"_id": 1, "x": {"a": 1, "b": 2}}],
        expected=[],
        msg="$in with object different key order on scalar field does NOT match",
    ),
    QueryTestCase(
        id="in_array_order_independence",
        filter={"x": {"$in": [3, 1]}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}],
        expected=[{"_id": 1, "x": 1}, {"_id": 3, "x": 3}],
        msg="$in matches regardless of value order in the array",
    ),
    QueryTestCase(
        id="dotted_path_array_of_objects",
        filter={"a.b": {"$in": [1]}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="$in on dotted path into array of objects matches",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_in_matching(collection, test_case):
    """Parametrized test for $in operator array and document matching behavior."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
