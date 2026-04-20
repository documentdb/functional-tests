"""
Tests for $ne field lookup patterns, null/missing handling, and edge cases.

Covers dot notation, nested fields, array indices, array of objects,
special field names, null/missing semantics, _id edge cases, and boundary values.
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
        id="embedded_doc_ne_includes_missing",
        filter={"carrier.fee": {"$ne": 1}},
        doc=[
            {"_id": 1, "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 2, "carrier": {"name": "Shipit", "fee": 1}},
            {"_id": 3},
        ],
        expected=[
            {"_id": 1, "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 3},
        ],
        msg="$ne on embedded field includes docs with missing field",
    ),
    QueryTestCase(
        id="embedded_doc_ne_no_match_excludes_none",
        filter={"carrier.fee": {"$ne": 999}},
        doc=[
            {"_id": 1, "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 2, "carrier": {"name": "Shipit", "fee": 1}},
            {"_id": 3},
        ],
        expected=[
            {"_id": 1, "carrier": {"name": "Shipit", "fee": 3}},
            {"_id": 2, "carrier": {"name": "Shipit", "fee": 1}},
            {"_id": 3},
        ],
        msg="$ne with value matching no docs excludes none",
    ),
    QueryTestCase(
        id="deep_nested_field",
        filter={"a.b.c": {"$ne": 1}},
        doc=[{"_id": 1, "a": {"b": {"c": 1}}}, {"_id": 2, "a": {"b": {"c": 2}}}],
        expected=[{"_id": 2, "a": {"b": {"c": 2}}}],
        msg="$ne on deep nested field",
    ),
    QueryTestCase(
        id="array_element_match",
        filter={"tags": {"$ne": "B"}},
        doc=[{"_id": 1, "tags": ["A", "B", "C"]}, {"_id": 2, "tags": ["D", "E"]}],
        expected=[{"_id": 2, "tags": ["D", "E"]}],
        msg="$ne on array field excludes if any element equals value",
    ),
    QueryTestCase(
        id="array_index_zero",
        filter={"arr.0": {"$ne": 10}},
        doc=[{"_id": 1, "arr": [10, 20]}, {"_id": 2, "arr": [30, 40]}],
        expected=[{"_id": 2, "arr": [30, 40]}],
        msg="$ne on array index 0",
    ),
    QueryTestCase(
        id="array_of_objects",
        filter={"a.b": {"$ne": 1}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}],
        expected=[{"_id": 2, "a": [{"b": 3}]}],
        msg="$ne on array of objects excludes if any element's field equals value",
    ),
    QueryTestCase(
        id="numeric_index_on_array",
        filter={"a.0.b": {"$ne": 1}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}],
        expected=[{"_id": 2, "a": [{"b": 3}]}],
        msg="$ne with numeric index path on array — a.0 resolves as array index at position 0",
    ),
    QueryTestCase(
        id="numeric_key_on_object",
        filter={"a.0.b": {"$ne": 1}},
        doc=[{"_id": 1, "a": {"0": {"b": 1}}}, {"_id": 2, "a": {"0": {"b": 2}}}],
        expected=[{"_id": 2, "a": {"0": {"b": 2}}}],
        msg="$ne with numeric key on object — a.0 resolves as object key '0', not array index",
    ),
    QueryTestCase(
        id="subdocument_different_field",
        filter={"a.x": {"$ne": 1}},
        doc=[{"_id": 1, "a": {"x": 1}}, {"_id": 2, "a": {"y": 1}}],
        expected=[{"_id": 2, "a": {"y": 1}}],
        msg="$ne on subdocument with different field name",
    ),
    QueryTestCase(
        id="nonexistent_field_with_value",
        filter={"missing": {"$ne": 1}},
        doc=[{"_id": 1, "a": 1}],
        expected=[{"_id": 1, "a": 1}],
        msg="$ne on non-existent field with non-null returns",
    ),
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_excludes_both_null_and_missing",
        filter={"a": {"$ne": None}},
        doc=[{"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 1}],
        expected=[{"_id": 3, "a": 1}],
        msg="$ne null excludes both null and missing fields",
    ),
    QueryTestCase(
        id="null_does_not_exclude_non_null",
        filter={"a": {"$ne": None}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": ""}, {"_id": 3, "a": False}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": ""}, {"_id": 3, "a": False}],
        msg="$ne null returns existing non-null fields",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="id_compound_document",
        filter={"_id": {"$ne": {"a": 1, "b": 2}}},
        doc=[{"_id": {"a": 1, "b": 2}, "x": 1}, {"_id": {"a": 3, "b": 4}, "x": 2}],
        expected=[{"_id": {"a": 3, "b": 4}, "x": 2}],
        msg="$ne on _id with compound document",
    ),
    QueryTestCase(
        id="id_with_null",
        filter={"_id": {"$ne": None}},
        doc=[{"_id": None, "a": 1}, {"_id": 1, "a": 2}],
        expected=[{"_id": 1, "a": 2}],
        msg="$ne on _id with null — excludes documents with _id: null",
    ),
    QueryTestCase(
        id="long_string",
        filter={"a": {"$ne": "x" * 10000}},
        doc=[{"_id": 1, "a": "x" * 10000}],
        expected=[],
        msg="$ne with very long string excludes same string",
    ),
    QueryTestCase(
        id="ne_with_empty_string",
        filter={"a": {"$ne": ""}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "x"}],
        expected=[{"_id": 2, "a": "x"}],
        msg="$ne with empty string is valid",
    ),
    QueryTestCase(
        id="ne_with_nested_empty_object",
        filter={"a": {"$ne": {"b": {}}}},
        doc=[{"_id": 1, "a": {"b": {}}}, {"_id": 2, "a": {"b": 1}}],
        expected=[{"_id": 2, "a": {"b": 1}}],
        msg="$ne with nested empty object is valid",
    ),
]


ALL_TESTS = FIELD_LOOKUP_TESTS + NULL_MISSING_TESTS + EDGE_CASE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ne_field_lookup(collection, test):
    """Parametrized test for $ne field lookup patterns."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
