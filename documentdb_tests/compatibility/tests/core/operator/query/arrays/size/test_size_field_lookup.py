"""
Tests for $size field lookup patterns.

Covers dotted paths through embedded documents, nested arrays with dotted paths,
array of embedded documents with dotted paths, deeply nested paths,
and non-existent paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOTTED_PATH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_field",
        filter={"a.b": {"$size": 2}},
        doc=[{"_id": 1, "a": {"b": [1, 2]}}],
        expected=[{"_id": 1, "a": {"b": [1, 2]}}],
        msg="$size on nested field a.b matches",
    ),
    QueryTestCase(
        id="deeply_nested",
        filter={"a.b.c": {"$size": 1}},
        doc=[{"_id": 1, "a": {"b": {"c": [1]}}}],
        expected=[{"_id": 1, "a": {"b": {"c": [1]}}}],
        msg="$size on deeply nested a.b.c matches",
    ),
    QueryTestCase(
        id="nonexistent_path",
        filter={"a.b.c": {"$size": 1}},
        doc=[{"_id": 1, "a": {"b": 1}}],
        expected=[],
        msg="$size on non-existent deeply nested path returns no matches",
    ),
    QueryTestCase(
        id="nonexistent_field",
        filter={"x": {"$size": 1}},
        doc=[{"_id": 1, "a": [1]}],
        expected=[],
        msg="$size on non-existent field returns no matches",
    ),
    QueryTestCase(
        id="dotted_path_not_array",
        filter={"a.b": {"$size": 1}},
        doc=[{"_id": 1, "a": {"b": "not_array"}}],
        expected=[],
        msg="$size on dotted path where value is not an array returns no matches",
    ),
    QueryTestCase(
        id="dotted_path_intermediate_null",
        filter={"a.b.c": {"$size": 0}},
        doc=[{"_id": 1, "a": {"b": None}}],
        expected=[],
        msg="$size on dotted path where intermediate field is null returns no match",
    ),
]

NESTED_ARRAY_DOTTED_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_array_dotted",
        filter={"a.b": {"$size": 2}},
        doc=[{"_id": 1, "a": {"b": [[1, 2], [3]]}}],
        expected=[{"_id": 1, "a": {"b": [[1, 2], [3]]}}],
        msg="$size on dotted path with nested arrays matches correct array",
    ),
    QueryTestCase(
        id="dotted_empty_array",
        filter={"a.b": {"$size": 0}},
        doc=[{"_id": 1, "a": {"b": []}}],
        expected=[{"_id": 1, "a": {"b": []}}],
        msg="$size 0 on dotted path matches embedded empty array",
    ),
    QueryTestCase(
        id="dotted_single_element",
        filter={"a.b": {"$size": 1}},
        doc=[{"_id": 1, "a": {"b": [99]}}],
        expected=[{"_id": 1, "a": {"b": [99]}}],
        msg="$size on dotted path through nested object matches single-element array",
    ),
]

ARRAY_OF_EMBEDDED_DOCS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="any_element_match",
        filter={"a.b": {"$size": 2}},
        doc=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3]}]}],
        expected=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3]}]}],
        msg="$size on dotted path through array of embedded docs"
        " matches if ANY element's sub-field has matching size",
    ),
    QueryTestCase(
        id="varying_sub_array_sizes",
        filter={"a.b": {"$size": 3}},
        doc=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3, 4, 5]}]}],
        expected=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3, 4, 5]}]}],
        msg="$size on dotted path matches when any embedded doc sub-array has matching size",
    ),
    QueryTestCase(
        id="no_element_match",
        filter={"a.b": {"$size": 4}},
        doc=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3]}]}],
        expected=[],
        msg="$size on dotted path returns no match"
        " when no embedded doc sub-array has matching size",
    ),
    QueryTestCase(
        id="deeply_nested_composite",
        filter={"a.b.c": {"$size": 2}},
        doc=[{"_id": 1, "a": [{"b": {"c": [1, 2]}}]}],
        expected=[{"_id": 1, "a": [{"b": {"c": [1, 2]}}]}],
        msg="$size on deeply nested dotted path through composite structures",
    ),
]

NUMERIC_INDEX_DOTTED_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_index_nested_field",
        filter={"a.0.b": {"$size": 2}},
        doc=[
            {"_id": 1, "a": [{"b": [1, 2]}, {"b": [3]}]},
            {"_id": 2, "a": [{"b": [1]}, {"b": [3, 4]}]},
        ],
        expected=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3]}]}],
        msg="$size on numeric index dot notation a.0.b matches first element's sub-field",
    ),
    QueryTestCase(
        id="numeric_index_out_of_bounds",
        filter={"a.5.b": {"$size": 1}},
        doc=[{"_id": 1, "a": [{"b": [1]}]}],
        expected=[],
        msg="$size on out-of-bounds numeric index returns no match",
    ),
    QueryTestCase(
        id="numeric_index_array_of_arrays",
        filter={"a.0.0": {"$size": 2}},
        doc=[{"_id": 1, "a": [[[1, 2]]]}],
        expected=[{"_id": 1, "a": [[[1, 2]]]}],
        msg="$size on a.0.0 traverses into array of arrays",
    ),
]

ALL_TESTS = (
    DOTTED_PATH_TESTS
    + NESTED_ARRAY_DOTTED_TESTS
    + ARRAY_OF_EMBEDDED_DOCS_TESTS
    + NUMERIC_INDEX_DOTTED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_size_field_lookup(collection, test):
    """Parametrized test for $size field lookup patterns."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
