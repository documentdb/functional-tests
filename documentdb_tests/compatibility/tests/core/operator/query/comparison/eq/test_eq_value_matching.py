"""
Tests for $eq value matching — arrays and objects.

Covers array exact/element matching, order and length sensitivity, dot-path
empty arrays, typed single-element arrays, and object field-order and shape
sensitivity.
"""

from datetime import datetime, timezone

import pytest
from bson import SON, Binary, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_order_matters",
        filter={"a": {"$eq": ["B", "A"]}},
        doc=[{"_id": 1, "a": ["A", "B"]}],
        expected=[],
        msg="$eq with array value — order matters",
    ),
    QueryTestCase(
        id="array_no_partial_match",
        filter={"a": {"$eq": ["A", "B"]}},
        doc=[{"_id": 1, "a": ["A", "B", "C"]}],
        expected=[],
        msg="$eq with array value does not partial match",
    ),
    QueryTestCase(
        id="array_matches_nested_array_element",
        filter={"a": {"$eq": ["A", "B"]}},
        doc=[{"_id": 1, "a": [["A", "B"], "C"]}],
        expected=[{"_id": 1, "a": [["A", "B"], "C"]}],
        msg="$eq with array value matches element that is an array",
    ),
    QueryTestCase(
        id="array_query_on_scalar_no_match",
        filter={"a": {"$eq": ["A", "B"]}},
        doc=[{"_id": 1, "a": "B"}, {"_id": 2, "a": "A"}],
        expected=[],
        msg="$eq with array value does NOT match scalar even if scalar is in array",
    ),
    QueryTestCase(
        id="empty_array_matches_nested_empty_element",
        filter={"a": {"$eq": []}},
        doc=[{"_id": 1, "a": [[]]}],
        expected=[{"_id": 1, "a": [[]]}],
        msg="$eq [] matches [[]] because [[]] contains element [] which equals []",
    ),
    QueryTestCase(
        id="scalar_no_match_in_array",
        filter={"a": {"$eq": 4}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[],
        msg="$eq scalar no match when not in array",
    ),
    QueryTestCase(
        id="scalar_on_nested_array_no_match",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        expected=[],
        msg="$eq scalar on array of arrays does NOT match (only one level traversal)",
    ),
    QueryTestCase(
        id="null_on_empty_array_no_match",
        filter={"a": {"$eq": None}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="$eq null on empty array does NOT match",
    ),
    QueryTestCase(
        id="array_different_length_longer",
        filter={"a": {"$eq": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [1, 2]}],
        expected=[],
        msg="$eq array [1,2,3] does not match [1,2]",
    ),
    QueryTestCase(
        id="array_exact_match",
        filter={"a": {"$eq": ["A", "B"]}},
        doc=[{"_id": 1, "a": ["A", "B"]}, {"_id": 2, "a": ["C", "D"]}],
        expected=[{"_id": 1, "a": ["A", "B"]}],
        msg="$eq with array value matches exact array",
    ),
    QueryTestCase(
        id="empty_array",
        filter={"a": {"$eq": []}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": []}],
        msg="$eq with empty array matches empty array",
    ),
    QueryTestCase(
        id="scalar_matches_array_containing_scalar",
        filter={"a": {"$eq": 1}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [4, 5]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$eq scalar matches array containing that scalar",
    ),
    QueryTestCase(
        id="array_on_array_of_arrays_matches",
        filter={"a": {"$eq": [1]}},
        doc=[{"_id": 1, "a": [[1], [2]]}],
        expected=[{"_id": 1, "a": [[1], [2]]}],
        msg="$eq array on array of arrays matches top-level element",
    ),
    QueryTestCase(
        id="null_on_array_containing_null",
        filter={"a": {"$eq": None}},
        doc=[{"_id": 1, "a": [1, None, 3]}],
        expected=[{"_id": 1, "a": [1, None, 3]}],
        msg="$eq null on array containing null matches",
    ),
    QueryTestCase(
        id="subdocument_with_array_cross_type",
        filter={"a.b": {"$eq": 1}},
        doc=[{"_id": 1, "a": {"b": [1, 2, 3]}}, {"_id": 2, "a": {"b": [4, 5]}}],
        expected=[{"_id": 1, "a": {"b": [1, 2, 3]}}],
        msg="$eq on subdocument with array matches element",
    ),
    QueryTestCase(
        id="array_of_subdocuments",
        filter={"a": {"$eq": [{"x": 1}, {"x": 2}]}},
        doc=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}, {"_id": 2, "a": [{"x": 3}]}],
        expected=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}],
        msg="$eq with array of subdocuments matches exact array",
    ),
    QueryTestCase(
        id="dot_path_empty_array",
        filter={"a.b": {"$eq": []}},
        doc=[{"_id": 1, "a": {"b": []}}, {"_id": 2, "a": {"b": [1]}}],
        expected=[{"_id": 1, "a": {"b": []}}],
        msg="$eq [] on a dot path matches a stored empty array at that nested path",
    ),
    QueryTestCase(
        id="single_element_int64_array",
        filter={"a": {"$eq": [Int64(5)]}},
        doc=[{"_id": 1, "a": [Int64(5)]}, {"_id": 2, "a": [Int64(6)]}],
        expected=[{"_id": 1, "a": [Int64(5)]}],
        msg="$eq matches a single-element array with a long (Int64) element",
    ),
    QueryTestCase(
        id="single_element_binary_array",
        filter={"a": {"$eq": [Binary(b"\x01", 0)]}},
        doc=[{"_id": 1, "a": [Binary(b"\x01", 0)]}, {"_id": 2, "a": [Binary(b"\x02", 0)]}],
        expected=[{"_id": 1, "a": [b"\x01"]}],
        msg="$eq matches a single-element array with a BinData element",
    ),
    QueryTestCase(
        id="single_element_date_array",
        filter={"a": {"$eq": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}},
        doc=[
            {"_id": 1, "a": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
            {"_id": 2, "a": [datetime(2025, 1, 1, tzinfo=timezone.utc)]},
        ],
        expected=[{"_id": 1, "a": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}],
        msg="$eq matches a single-element array with a date element",
    ),
    QueryTestCase(
        id="single_element_objectid_array",
        filter={"a": {"$eq": [ObjectId("507f1f77bcf86cd799439011")]}},
        doc=[
            {"_id": 1, "a": [ObjectId("507f1f77bcf86cd799439011")]},
            {"_id": 2, "a": [ObjectId("507f1f77bcf86cd799439012")]},
        ],
        expected=[{"_id": 1, "a": [ObjectId("507f1f77bcf86cd799439011")]}],
        msg="$eq matches a single-element array with an ObjectId element",
    ),
]

OBJECT_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_order_no_match",
        filter={"a": {"$eq": SON([("y", 2), ("x", 1)])}},
        doc=[{"_id": 1, "a": SON([("x", 1), ("y", 2)])}],
        expected=[],
        msg="$eq document does NOT match with different field order",
    ),
    QueryTestCase(
        id="extra_field_no_match",
        filter={"a": {"$eq": {"x": 1, "y": 2}}},
        doc=[{"_id": 1, "a": {"x": 1, "y": 2, "z": 3}}],
        expected=[],
        msg="$eq document with extra field does NOT match",
    ),
    QueryTestCase(
        id="missing_field_no_match",
        filter={"a": {"$eq": {"x": 1, "y": 2, "z": 3}}},
        doc=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        expected=[],
        msg="$eq document with missing field does NOT match",
    ),
    QueryTestCase(
        id="nested_field_order_matters",
        filter={"a": {"$eq": {"b": SON([("y", 2), ("x", 1)])}}},
        doc=[{"_id": 1, "a": {"b": SON([("x", 1), ("y", 2)])}}],
        expected=[],
        msg="$eq nested document field order matters",
    ),
    QueryTestCase(
        id="nested_document_value_differs",
        filter={"a": {"$eq": {"b": {"c": 2}}}},
        doc=[{"_id": 1, "a": {"b": {"c": 1}}}],
        expected=[],
        msg="$eq nested document does NOT match when nested value differs",
    ),
    QueryTestCase(
        id="field_order_match",
        filter={"a": {"$eq": SON([("x", 1), ("y", 2)])}},
        doc=[{"_id": 1, "a": SON([("x", 1), ("y", 2)])}],
        expected=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        msg="$eq document matches with same field order",
    ),
    QueryTestCase(
        id="nested_document",
        filter={"a": {"$eq": {"b": {"c": 1}}}},
        doc=[{"_id": 1, "a": {"b": {"c": 1}}}, {"_id": 2, "a": {"b": {"c": 2}}}],
        expected=[{"_id": 1, "a": {"b": {"c": 1}}}],
        msg="$eq with nested document matches exact structure",
    ),
    QueryTestCase(
        id="empty_document",
        filter={"a": {"$eq": {}}},
        doc=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 1}}],
        expected=[{"_id": 1, "a": {}}],
        msg="$eq with empty document matches empty document",
    ),
    QueryTestCase(
        id="dollar_prefixed_value",
        filter={"a": {"$eq": {"$x": 1, "$y": 2}}},
        doc=[{"_id": 1, "a": {"$x": 1, "$y": 2}}],
        expected=[{"_id": 1, "a": {"$x": 1, "$y": 2}}],
        msg="$eq with dollar-prefixed keys in value matches stored document",
    ),
]


ALL_TESTS = ARRAY_MATCHING_TESTS + OBJECT_MATCHING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_eq_value_matching(collection, test):
    """Parametrized test for $eq array and object value matching."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
