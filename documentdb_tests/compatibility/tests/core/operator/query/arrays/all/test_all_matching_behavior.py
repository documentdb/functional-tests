"""
Tests for $all query operator matching behavior.

Validates scalar matching, order independence, duplicate handling,
empty string, array field implicit matching, object/document matching,
nested array behavior, null/missing field handling, field lookup patterns,
and large arrays.

"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SCALAR_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="scalar_multi_no_match",
        filter={"a": {"$all": ["x", "y"]}},
        doc=[{"_id": 1, "a": "x"}],
        expected=[],
        msg="Multi-element $all should not match scalar field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SCALAR_MATCHING_TESTS))
def test_all_scalar_matching(collection, test):
    """Test $all matching against scalar (non-array) fields."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


ORDER_INDEPENDENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="reverse_order",
        filter={"a": {"$all": ["x", "y"]}},
        doc=[{"_id": 1, "a": ["y", "x"]}, {"_id": 2, "a": ["x"]}],
        expected=[{"_id": 1, "a": ["y", "x"]}],
        msg="$all should match regardless of element order in field",
    ),
    QueryTestCase(
        id="extra_elements_different_order",
        filter={"a": {"$all": ["x", "y"]}},
        doc=[{"_id": 1, "a": ["x", "z", "y"]}],
        expected=[{"_id": 1, "a": ["x", "z", "y"]}],
        msg="$all should match with extra elements in different order",
    ),
    QueryTestCase(
        id="numeric_order",
        filter={"a": {"$all": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [3, 1, 2]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [3, 1, 2]}],
        msg="$all should match numeric arrays regardless of order",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ORDER_INDEPENDENCE_TESTS))
def test_all_order_independence(collection, test):
    """Test $all matches regardless of element order in the field."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


DUPLICATE_HANDLING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="dup_in_all_single_in_field",
        filter={"a": {"$all": ["x", "x"]}},
        doc=[{"_id": 1, "a": ["x"]}, {"_id": 2, "a": ["y"]}],
        expected=[{"_id": 1, "a": ["x"]}],
        msg="Duplicate in $all, single in field should match",
    ),
    QueryTestCase(
        id="single_in_all_dup_in_field",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": ["x", "x"]}],
        expected=[{"_id": 1, "a": ["x", "x"]}],
        msg="Single in $all, duplicate in field should match",
    ),
    QueryTestCase(
        id="dup_in_all_multi_in_field",
        filter={"a": {"$all": ["x", "x", "y"]}},
        doc=[{"_id": 1, "a": ["x", "y"]}, {"_id": 2, "a": ["x"]}],
        expected=[{"_id": 1, "a": ["x", "y"]}],
        msg="Duplicates in $all with multi-element field should match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DUPLICATE_HANDLING_TESTS))
def test_all_duplicate_handling(collection, test):
    """Test $all duplicate handling in both $all array and field array."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


EMPTY_STRING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_string_in_array",
        filter={"a": {"$all": [""]}},
        doc=[{"_id": 1, "a": ["", "x"]}, {"_id": 2, "a": ["x"]}],
        expected=[{"_id": 1, "a": ["", "x"]}],
        msg="$all with empty string should match array containing empty string",
    ),
    QueryTestCase(
        id="empty_string_not_null",
        filter={"a": {"$all": [""]}},
        doc=[{"_id": 1, "a": [None]}],
        expected=[],
        msg="$all with empty string should not match null",
    ),
    QueryTestCase(
        id="empty_string_scalar",
        filter={"a": {"$all": [""]}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "x"}],
        expected=[{"_id": 1, "a": ""}],
        msg="$all with empty string should match scalar empty string",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMPTY_STRING_TESTS))
def test_all_empty_string(collection, test):
    """Test $all matching with empty string values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


ARRAY_IMPLICIT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="all_present",
        filter={"a": {"$all": ["x", "y"]}},
        doc=[{"_id": 1, "a": ["x", "y", "z"]}],
        expected=[{"_id": 1, "a": ["x", "y", "z"]}],
        msg="Should match when all elements present with extras",
    ),
    QueryTestCase(
        id="some_present",
        filter={"a": {"$all": ["x", "y"]}},
        doc=[{"_id": 1, "a": ["x", "z"]}],
        expected=[],
        msg="Should not match when only some elements present",
    ),
    QueryTestCase(
        id="empty_array_field",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="Should not match empty array field",
    ),
    QueryTestCase(
        id="basic_two_elements",
        filter={"a": {"$all": ["x", "y"]}},
        doc=[
            {"_id": 1, "a": ["x", "y", "z"]},
            {"_id": 2, "a": ["x", "z"]},
            {"_id": 3, "a": ["y", "z"]},
        ],
        expected=[{"_id": 1, "a": ["x", "y", "z"]}],
        msg="$all with two elements should match only documents containing both",
    ),
    QueryTestCase(
        id="element_not_present",
        filter={"a": {"$all": ["z"]}},
        doc=[{"_id": 1, "a": ["x"]}, {"_id": 2, "a": ["y"]}],
        expected=[],
        msg="$all with element not present in any document should return zero results",
    ),
    QueryTestCase(
        id="int64_values",
        filter={"a": {"$all": [Int64(1), Int64(2), Int64(3)]}},
        doc=[
            {"_id": 1, "a": [Int64(1), Int64(2), Int64(3)]},
            {"_id": 2, "a": [Int64(1), Int64(2)]},
        ],
        expected=[{"_id": 1, "a": [Int64(1), Int64(2), Int64(3)]}],
        msg="$all with Int64 values should match array field",
    ),
    QueryTestCase(
        id="decimal128_values",
        filter={"a": {"$all": [Decimal128("1"), Decimal128("2"), Decimal128("3")]}},
        doc=[
            {"_id": 1, "a": [Decimal128("1"), Decimal128("2"), Decimal128("3")]},
            {"_id": 2, "a": [Decimal128("1")]},
        ],
        expected=[{"_id": 1, "a": [Decimal128("1"), Decimal128("2"), Decimal128("3")]}],
        msg="$all with Decimal128 values should match array field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_IMPLICIT_TESTS))
def test_all_array_implicit_matching(collection, test):
    """Test $all implicit matching on array fields."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


OBJECT_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="exact_object_match",
        filter={"a": {"$all": [{"x": 1, "y": 2}]}},
        doc=[
            {"_id": 1, "a": [{"x": 1, "y": 2}]},
            {"_id": 2, "a": [{"x": 1}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2}]}],
        msg="Should match exact embedded document",
    ),
    QueryTestCase(
        id="field_order_matters",
        filter={"a": {"$all": [{"x": 1, "y": 2}]}},
        doc=[{"_id": 1, "a": [{"y": 2, "x": 1}]}],
        expected=[],
        msg="Field order matters in BSON document comparison",
    ),
    QueryTestCase(
        id="partial_match_insufficient",
        filter={"a": {"$all": [{"x": 1}]}},
        doc=[{"_id": 1, "a": [{"x": 1, "y": 2}]}],
        expected=[],
        msg="Partial document match should not be sufficient",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OBJECT_MATCHING_TESTS))
def test_all_object_matching(collection, test):
    """Test $all matching with embedded documents."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


NESTED_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_array_as_element",
        filter={"a": {"$all": [["ssl", "security"]]}},
        doc=[
            {"_id": 1, "a": [["ssl", "security"], "other"]},
            {"_id": 2, "a": ["ssl", "security"]},
        ],
        expected=[
            {"_id": 1, "a": [["ssl", "security"], "other"]},
            {"_id": 2, "a": ["ssl", "security"]},
        ],
        msg="Nested array in $all should match field containing it as element or equal to it",
    ),
    QueryTestCase(
        id="nested_single_element",
        filter={"a": {"$all": [["A"]]}},
        doc=[{"_id": 1, "a": [["A"], "B"]}, {"_id": 2, "a": [["B"]]}],
        expected=[{"_id": 1, "a": [["A"], "B"]}],
        msg="Nested single-element array should match as element",
    ),
    QueryTestCase(
        id="nested_matches_equal_field",
        filter={"a": {"$all": [["A"]]}},
        doc=[{"_id": 1, "a": ["A"]}, {"_id": 2, "a": ["B"]}],
        expected=[{"_id": 1, "a": ["A"]}],
        msg="Nested array in $all should match field equal to the inner array",
    ),
    QueryTestCase(
        id="multiple_nested_arrays_match",
        filter={"a": {"$all": [["A"], ["B"]]}},
        doc=[{"_id": 1, "a": [["A"], ["B"], "C"]}, {"_id": 2, "a": [["A"]]}],
        expected=[{"_id": 1, "a": [["A"], ["B"], "C"]}],
        msg="Multiple nested arrays in $all should all be required",
    ),
    QueryTestCase(
        id="multiple_nested_arrays_no_match",
        filter={"a": {"$all": [["A"], ["B"]]}},
        doc=[{"_id": 1, "a": [["A"]]}],
        expected=[],
        msg="Missing nested array should not match",
    ),
    QueryTestCase(
        id="deeply_nested",
        filter={"a": {"$all": [[[1]]]}},
        doc=[{"_id": 1, "a": [[[1]], "x"]}, {"_id": 2, "a": [[1]]}],
        expected=[{"_id": 1, "a": [[[1]], "x"]}, {"_id": 2, "a": [[1]]}],
        msg="Deeply nested array should match as element or equal",
    ),
    QueryTestCase(
        id="nested_with_duplicates_match",
        filter={"a": {"$all": [["A", "A"]]}},
        doc=[{"_id": 1, "a": [["A", "A"]]}, {"_id": 2, "a": [["A"]]}],
        expected=[{"_id": 1, "a": [["A", "A"]]}],
        msg="Nested array with duplicates should require exact match",
    ),
    QueryTestCase(
        id="nested_with_duplicates_no_match",
        filter={"a": {"$all": [["A", "A"]]}},
        doc=[{"_id": 1, "a": [["A"]]}],
        expected=[],
        msg="Nested array with duplicates should not match shorter array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_ARRAY_TESTS))
def test_all_nested_arrays(collection, test):
    """Test $all matching with nested arrays."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


NULL_AND_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_field_is_null",
        filter={"a": {"$all": [None]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": None}],
        msg="$all [null] should match field set to null",
    ),
    QueryTestCase(
        id="null_field_is_missing",
        filter={"a": {"$all": [None]}},
        doc=[{"_id": 1, "b": 1}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "b": 1}],
        msg="$all [null] should match document where field is missing",
    ),
    QueryTestCase(
        id="null_array_contains_null",
        filter={"a": {"$all": [None]}},
        doc=[{"_id": 1, "a": [None, 1]}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": [None, 1]}],
        msg="$all [null] should match array containing null",
    ),
    QueryTestCase(
        id="null_and_value",
        filter={"a": {"$all": [None, "x"]}},
        doc=[{"_id": 1, "a": ["x", None]}, {"_id": 2, "a": ["x"]}],
        expected=[{"_id": 1, "a": ["x", None]}],
        msg="$all [null, value] should match array containing both",
    ),
    QueryTestCase(
        id="null_on_empty_array",
        filter={"a": {"$all": [None]}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [None]}],
        expected=[{"_id": 2, "a": [None]}],
        msg="$all [null] should not match empty array",
    ),
    QueryTestCase(
        id="null_and_int_missing_null",
        filter={"a": {"$all": [None, 1]}},
        doc=[{"_id": 1, "a": [1]}, {"_id": 2, "a": [None, 1]}],
        expected=[{"_id": 2, "a": [None, 1]}],
        msg="$all [null, 1] should not match [1] (missing null element)",
    ),
    QueryTestCase(
        id="null_distinguishes_null_vs_missing",
        filter={"a": {"$all": [None]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 1}],
        expected=[{"_id": 1, "a": None}, {"_id": 2}],
        msg="$all [null] should match both null field and missing field",
    ),
    QueryTestCase(
        id="nonexistent_field",
        filter={"z": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": ["x"]}],
        expected=[],
        msg="$all on non-existent field should return no matches",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_AND_MISSING_TESTS))
def test_all_null_and_missing(collection, test):
    """Test $all behavior with null values and missing fields."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


LARGE_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="10000_elements_match",
        filter={"a": {"$all": list(range(10000))}},
        doc=[{"_id": 1, "a": list(range(10000))}],
        expected=[{"_id": 1, "a": list(range(10000))}],
        msg="$all with 10000 elements should match field with 10000 matching elements",
    ),
    QueryTestCase(
        id="1_element_on_1000_field",
        filter={"a": {"$all": [500]}},
        doc=[{"_id": 1, "a": list(range(1000))}],
        expected=[{"_id": 1, "a": list(range(1000))}],
        msg="$all with 1 element should match field with 1000 elements",
    ),
    QueryTestCase(
        id="10000_elements_missing_one",
        filter={"a": {"$all": list(range(10000))}},
        doc=[{"_id": 1, "a": list(range(9999))}],
        expected=[],
        msg="$all with 10000 elements should not match field missing one element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LARGE_ARRAY_TESTS))
def test_all_large_arrays(collection, test):
    """Test $all with large arrays."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


FIELD_LOOKUP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_of_docs_path",
        filter={"a.b": {"$all": [1, 2]}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 1}]}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="$all on dotted path through array of embedded docs should match across elements",
    ),
    QueryTestCase(
        id="deeply_nested_field_path",
        filter={"a.b.c": {"$all": ["x"]}},
        doc=[
            {"_id": 1, "a": {"b": {"c": ["x", "y"]}}},
            {"_id": 2, "a": {"b": {"c": ["y"]}}},
        ],
        expected=[{"_id": 1, "a": {"b": {"c": ["x", "y"]}}}],
        msg="$all on deeply nested field should work",
    ),
    QueryTestCase(
        id="numeric_path_component",
        filter={"a.0.b": {"$all": [1]}},
        doc=[
            {"_id": 1, "a": [{"b": 1}]},
            {"_id": 2, "a": {"0": {"b": 1}}},
            {"_id": 3, "a": [{"b": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"b": 1}]}, {"_id": 2, "a": {"0": {"b": 1}}}],
        msg="$all on numeric path component should match both array index and object key",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_LOOKUP_TESTS))
def test_all_field_lookup(collection, test):
    """Test $all with various field lookup patterns."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
