"""
Tests for $eq field lookup patterns, null/missing handling, and boundary values.

Covers dot notation, array/object indexing, null vs missing semantics,
and _id and string boundary values.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

FIELD_LOOKUP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_field",
        filter={"a.b": {"$eq": 1}},
        doc=[{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}],
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="$eq on nested field using dot notation",
    ),
    QueryTestCase(
        id="deep_nested_field",
        filter={"a.b.c": {"$eq": 1}},
        doc=[{"_id": 1, "a": {"b": {"c": 1}}}, {"_id": 2, "a": {"b": {"c": 2}}}],
        expected=[{"_id": 1, "a": {"b": {"c": 1}}}],
        msg="$eq on deep nested field",
    ),
    QueryTestCase(
        id="array_element_match",
        filter={"tags": {"$eq": "B"}},
        doc=[{"_id": 1, "tags": ["A", "B", "C"]}, {"_id": 2, "tags": ["D", "E"]}],
        expected=[{"_id": 1, "tags": ["A", "B", "C"]}],
        msg="$eq on array field matches if any element equals value",
    ),
    QueryTestCase(
        id="array_index_zero",
        filter={"arr.0": {"$eq": 10}},
        doc=[{"_id": 1, "arr": [10, 20]}, {"_id": 2, "arr": [30, 40]}],
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="$eq on array index 0",
    ),
    QueryTestCase(
        id="array_index_one",
        filter={"arr.1": {"$eq": 20}},
        doc=[{"_id": 1, "arr": [10, 20]}, {"_id": 2, "arr": [30, 40]}],
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="$eq on array index 1",
    ),
    QueryTestCase(
        id="array_of_objects",
        filter={"a.b": {"$eq": 1}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="$eq on array of objects matches if any element's field equals value",
    ),
    QueryTestCase(
        id="numeric_index_on_array",
        filter={"a.0.b": {"$eq": 1}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="$eq with numeric index path on array",
    ),
    QueryTestCase(
        id="numeric_key_on_object",
        filter={"a.0.b": {"$eq": 1}},
        doc=[{"_id": 1, "a": {"0": {"b": 1}}}, {"_id": 2, "a": {"0": {"b": 2}}}],
        expected=[{"_id": 1, "a": {"0": {"b": 1}}}],
        msg="$eq with numeric key on object (not array)",
    ),
    QueryTestCase(
        id="subdocument_different_field",
        filter={"a.x": {"$eq": 1}},
        doc=[{"_id": 1, "a": {"x": 1}}, {"_id": 2, "a": {"y": 1}}],
        expected=[{"_id": 1, "a": {"x": 1}}],
        msg="$eq on subdocument with different field name",
    ),
    QueryTestCase(
        id="dollar_prefixed_field_name",
        filter={"a": {"$eq": {"$type": "special"}}},
        doc=[{"_id": 1, "a": {"$type": "special"}}, {"_id": 2, "a": {"$type": "other"}}],
        expected=[{"_id": 1, "a": {"$type": "special"}}],
        msg="$eq with dollar-prefixed keys in query value is allowed",
    ),
    QueryTestCase(
        id="array_element_no_match",
        filter={"tags": {"$eq": "D"}},
        doc=[{"_id": 1, "tags": ["A", "B", "C"]}],
        expected=[],
        msg="$eq on array field no match when element not present",
    ),
    QueryTestCase(
        id="array_of_objects_no_match",
        filter={"a.b": {"$eq": 3}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        expected=[],
        msg="$eq on array of objects no match",
    ),
    QueryTestCase(
        id="nonexistent_field_with_null",
        filter={"missing": {"$eq": None}},
        doc=[{"_id": 1, "a": 1}],
        expected=[{"_id": 1, "a": 1}],
        msg="$eq on non-existent field with null matches",
    ),
    QueryTestCase(
        id="nonexistent_field_with_value",
        filter={"missing": {"$eq": 1}},
        doc=[{"_id": 1, "a": 1}],
        expected=[],
        msg="$eq on non-existent field with non-null does not match",
    ),
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_matches_both_null_and_missing",
        filter={"a": {"$eq": None}},
        doc=[{"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 1}],
        expected=[{"_id": 1, "a": None}, {"_id": 2}],
        msg="$eq null matches both null and missing fields",
    ),
    QueryTestCase(
        id="null_does_not_match_non_null",
        filter={"a": {"$eq": None}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": ""}, {"_id": 3, "a": False}],
        expected=[],
        msg="$eq null does NOT match existing non-null field",
    ),
    QueryTestCase(
        id="nested_null_matches_missing_leaf_under_present_parent",
        filter={"a.b": {"$eq": None}},
        doc=[
            {"_id": 1, "a": {}},
            {"_id": 2, "a": {"x": 1}},
            {"_id": 3, "a": {"b": None}},
            {"_id": 4, "a": {"b": 1}},
        ],
        expected=[
            {"_id": 1, "a": {}},
            {"_id": 2, "a": {"x": 1}},
            {"_id": 3, "a": {"b": None}},
        ],
        msg="$eq null on dot path matches a missing leaf or explicit null, not a non-null value",
    ),
    QueryTestCase(
        id="nested_null_matches_array_element_missing_key",
        filter={"a.b": {"$eq": None}},
        doc=[
            {"_id": 1, "a": [{"b": 1}, {"c": 2}]},
            {"_id": 2, "a": [{"b": 1}, {"b": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"b": 1}, {"c": 2}]}],
        msg="$eq null on dot path into array-of-objects matches when any element lacks the key",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="id_compound_document",
        filter={"_id": {"$eq": {"a": 1, "b": 2}}},
        doc=[{"_id": {"a": 1, "b": 2}, "x": 1}, {"_id": {"a": 3, "b": 4}, "x": 2}],
        expected=[{"_id": {"a": 1, "b": 2}, "x": 1}],
        msg="$eq on _id with compound document",
    ),
    QueryTestCase(
        id="id_with_null",
        filter={"_id": {"$eq": None}},
        doc=[{"_id": None, "a": 1}, {"_id": 1, "a": 2}],
        expected=[{"_id": None, "a": 1}],
        msg="$eq on _id with null — matches documents with _id: null only",
    ),
    QueryTestCase(
        id="long_string",
        filter={"a": {"$eq": "x" * 10000}},
        doc=[{"_id": 1, "a": "x" * 10000}],
        expected=[{"_id": 1, "a": "x" * 10000}],
        msg="$eq with very long string matches same string",
    ),
    QueryTestCase(
        id="eq_with_empty_string",
        filter={"a": {"$eq": ""}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "x"}],
        expected=[{"_id": 1, "a": ""}],
        msg="$eq with empty string is valid",
    ),
    QueryTestCase(
        id="eq_with_nested_empty_object",
        filter={"a": {"$eq": {"b": {}}}},
        doc=[{"_id": 1, "a": {"b": {}}}, {"_id": 2, "a": {"b": 1}}],
        expected=[{"_id": 1, "a": {"b": {}}}],
        msg="$eq with nested empty object is valid",
    ),
]


ALL_TESTS = FIELD_LOOKUP_TESTS + NULL_MISSING_TESTS + EDGE_CASE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_eq_field_lookup(collection, test):
    """Parametrized test for $eq field lookup, null/missing handling, and boundary values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
