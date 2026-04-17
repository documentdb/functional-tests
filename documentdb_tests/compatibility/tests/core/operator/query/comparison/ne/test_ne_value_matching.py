"""
Tests for $ne value matching.

Covers exact array match, array order sensitivity, scalar vs array matching,
nested array traversal, array element matching, object field order sensitivity,
extra/missing fields, nested documents, empty documents, dollar-prefixed values,
NaN/Infinity handling, and collation behavior.
"""

import pytest
from bson import SON, Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_order_matters",
        filter={"a": {"$ne": ["B", "A"]}},
        doc=[{"_id": 1, "a": ["A", "B"]}],
        expected=[{"_id": 1, "a": ["A", "B"]}],
        msg="$ne with array value — order matters, different order should return",
    ),
    QueryTestCase(
        id="array_no_partial_match",
        filter={"a": {"$ne": ["A", "B"]}},
        doc=[{"_id": 1, "a": ["A", "B", "C"]}],
        expected=[{"_id": 1, "a": ["A", "B", "C"]}],
        msg="$ne with array value does not partial match — should return",
    ),
    QueryTestCase(
        id="array_matches_nested_array_element",
        filter={"a": {"$ne": ["A", "B"]}},
        doc=[{"_id": 1, "a": [["A", "B"], "C"]}],
        expected=[],
        msg="$ne with array value matches element that is an array — should NOT return",
    ),
    QueryTestCase(
        id="array_query_on_scalar_no_match",
        filter={"a": {"$ne": ["A", "B"]}},
        doc=[{"_id": 1, "a": "B"}, {"_id": 2, "a": "A"}],
        expected=[{"_id": 1, "a": "B"}, {"_id": 2, "a": "A"}],
        msg="$ne with array value does NOT match scalar — should return all",
    ),
    QueryTestCase(
        id="empty_array_does_not_match_nested_empty",
        filter={"a": {"$ne": []}},
        doc=[{"_id": 1, "a": [[]]}],
        expected=[],
        msg="$ne [] against [[]] — [[]] contains element [] which equals [], should NOT return",
    ),
    QueryTestCase(
        id="scalar_no_match_in_array",
        filter={"a": {"$ne": 4}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$ne scalar no match when not in array — should return",
    ),
    QueryTestCase(
        id="scalar_on_nested_array_no_match",
        filter={"a": {"$ne": 1}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        expected=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        msg="$ne scalar on array of arrays — only one level traversal, should return",
    ),
    QueryTestCase(
        id="null_on_empty_array_no_match",
        filter={"a": {"$ne": None}},
        doc=[{"_id": 1, "a": []}],
        expected=[{"_id": 1, "a": []}],
        msg="$ne null on empty array — null not in empty array, should return",
    ),
    QueryTestCase(
        id="array_exact_match",
        filter={"a": {"$ne": ["A", "B"]}},
        doc=[{"_id": 1, "a": ["A", "B"]}, {"_id": 2, "a": ["C", "D"]}],
        expected=[{"_id": 2, "a": ["C", "D"]}],
        msg="$ne with array value excludes exact array match",
    ),
    QueryTestCase(
        id="empty_array",
        filter={"a": {"$ne": []}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 2, "a": [1]}],
        msg="$ne with empty array excludes empty array",
    ),
    QueryTestCase(
        id="scalar_matches_array_containing_scalar",
        filter={"a": {"$ne": 1}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [4, 5]}],
        expected=[{"_id": 2, "a": [4, 5]}],
        msg="$ne scalar excludes array containing that scalar",
    ),
    QueryTestCase(
        id="array_on_array_of_arrays_matches",
        filter={"a": {"$ne": [1]}},
        doc=[{"_id": 1, "a": [[1], [2]]}],
        expected=[],
        msg="$ne array on array of arrays — top-level element matches, should NOT return",
    ),
    QueryTestCase(
        id="null_on_array_containing_null",
        filter={"a": {"$ne": None}},
        doc=[{"_id": 1, "a": [1, None, 3]}],
        expected=[],
        msg="$ne null on array containing null — should NOT return",
    ),
    QueryTestCase(
        id="subdocument_with_array_cross_type",
        filter={"a.b": {"$ne": 1}},
        doc=[{"_id": 1, "a": {"b": [1, 2, 3]}}, {"_id": 2, "a": {"b": [4, 5]}}],
        expected=[{"_id": 2, "a": {"b": [4, 5]}}],
        msg="$ne on subdocument with array excludes element match",
    ),
    QueryTestCase(
        id="array_of_subdocuments",
        filter={"a": {"$ne": [{"x": 1}, {"x": 2}]}},
        doc=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}, {"_id": 2, "a": [{"x": 3}]}],
        expected=[{"_id": 2, "a": [{"x": 3}]}],
        msg="$ne with array of subdocuments excludes exact array match",
    ),
]

OBJECT_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_order_no_match",
        filter={"a": {"$ne": SON([("y", 2), ("x", 1)])}},
        doc=[{"_id": 1, "a": SON([("x", 1), ("y", 2)])}],
        expected=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        msg="$ne document with different field order — should return",
    ),
    QueryTestCase(
        id="extra_field_no_match",
        filter={"a": {"$ne": {"x": 1, "y": 2}}},
        doc=[{"_id": 1, "a": {"x": 1, "y": 2, "z": 3}}],
        expected=[{"_id": 1, "a": {"x": 1, "y": 2, "z": 3}}],
        msg="$ne document with extra field — should return",
    ),
    QueryTestCase(
        id="field_order_match",
        filter={"a": {"$ne": SON([("x", 1), ("y", 2)])}},
        doc=[{"_id": 1, "a": SON([("x", 1), ("y", 2)])}],
        expected=[],
        msg="$ne document with same field order — should NOT return",
    ),
    QueryTestCase(
        id="nested_document",
        filter={"a": {"$ne": {"b": {"c": 1}}}},
        doc=[{"_id": 1, "a": {"b": {"c": 1}}}, {"_id": 2, "a": {"b": {"c": 2}}}],
        expected=[{"_id": 2, "a": {"b": {"c": 2}}}],
        msg="$ne with nested document excludes exact structure match",
    ),
    QueryTestCase(
        id="empty_document",
        filter={"a": {"$ne": {}}},
        doc=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 1}}],
        expected=[{"_id": 2, "a": {"x": 1}}],
        msg="$ne with empty document excludes empty document",
    ),
    QueryTestCase(
        id="dollar_prefixed_value",
        filter={"a": {"$ne": {"$x": 1, "$y": 2}}},
        doc=[{"_id": 1, "a": {"$x": 1, "$y": 2}}],
        expected=[],
        msg="$ne with dollar-prefixed keys in value — exact match, should NOT return",
    ),
]


NAN_INFINITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_cross_type_decimal128",
        filter={"a": {"$ne": Decimal128("NaN")}},
        doc=[{"_id": 1, "a": float("nan")}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$ne Decimal128 NaN cross-type excludes float NaN",
    ),
    QueryTestCase(
        id="infinity_vs_negative_infinity",
        filter={"a": {"$ne": float("-inf")}},
        doc=[{"_id": 1, "a": float("inf")}, {"_id": 2, "a": float("-inf")}],
        expected=[{"_id": 1, "a": float("inf")}],
        msg="$ne -Infinity returns document with Infinity",
    ),
]

COLLATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="without_collation_case_sensitive",
        filter={"a": {"$ne": "abc"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "ABC"}, {"_id": 3, "a": "Abc"}],
        expected=[{"_id": 2, "a": "ABC"}, {"_id": 3, "a": "Abc"}],
        msg="$ne without collation is case-sensitive",
    ),
]


UNICODE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="multi_byte_utf8",
        filter={"a": {"$ne": "café"}},
        doc=[{"_id": 1, "a": "café"}, {"_id": 2, "a": "cafe"}],
        expected=[{"_id": 2, "a": "cafe"}],
        msg="$ne with multi-byte UTF-8 string excludes exact match",
    ),
]

REGEX_IN_FIELD_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="regex_pattern_as_string_value",
        filter={"a": {"$ne": "^abc"}},
        doc=[{"_id": 1, "a": "^abc"}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$ne with regex-like string treats it as literal string, not regex",
    ),
]


ALL_TESTS = (
    ARRAY_MATCHING_TESTS
    + OBJECT_MATCHING_TESTS
    + NAN_INFINITY_TESTS
    + COLLATION_TESTS
    + UNICODE_TESTS
    + REGEX_IN_FIELD_VALUE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ne_value_matching(collection, test):
    """Parametrized test for $ne value matching."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
