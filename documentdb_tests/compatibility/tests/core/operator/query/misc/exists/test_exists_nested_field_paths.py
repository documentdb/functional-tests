"""
Tests for $exists with nested field paths (dot notation).

Covers simple nested objects, deep paths, array traversal, array indices,
numeric keys on objects, path traversal through non-objects, and special characters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SIMPLE_NESTED_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_exists",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": {"b": 1}}],
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="Dot notation matches nested field",
    ),
    QueryTestCase(
        id="nested_not_exists",
        filter={"a.b": {"$exists": False}},
        doc=[{"_id": 1, "a": {"c": 1}}],
        expected=[{"_id": 1, "a": {"c": 1}}],
        msg="Dot notation matches when nested field absent",
    ),
    QueryTestCase(
        id="nested_null_exists",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": {"b": None}}],
        expected=[{"_id": 1, "a": {"b": None}}],
        msg="Dot notation matches nested null field (field exists)",
    ),
    QueryTestCase(
        id="empty_object_parent_false",
        filter={"a.b": {"$exists": False}},
        doc=[{"_id": 1, "a": {}}],
        expected=[{"_id": 1, "a": {}}],
        msg="Empty object parent — nested field does not exist",
    ),
    QueryTestCase(
        id="empty_object_parent_true",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": {}}],
        expected=[],
        msg="Empty object parent — nested field does not match",
    ),
]

DEEP_NESTED_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="deep_nested_exists",
        filter={"a.b.c.d": {"$exists": True}},
        doc=[{"_id": 1, "a": {"b": {"c": {"d": 1}}}}],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": 1}}}}],
        msg="Deep dot notation matches",
    ),
    QueryTestCase(
        id="deep_nested_not_exists",
        filter={"a.b.c.d": {"$exists": False}},
        doc=[{"_id": 1, "a": {"b": {"c": 1}}}],
        expected=[{"_id": 1, "a": {"b": {"c": 1}}}],
        msg="Deep dot notation matches when path incomplete",
    ),
]

ARRAY_PATH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_dot_all_have_field",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="Dot notation through array matches when elements have field",
    ),
    QueryTestCase(
        id="array_dot_none_have_field",
        filter={"a.b": {"$exists": False}},
        doc=[{"_id": 1, "a": [{"c": 1}, {"c": 2}]}],
        expected=[{"_id": 1, "a": [{"c": 1}, {"c": 2}]}],
        msg="Dot notation through array matches false when no element has field",
    ),
    QueryTestCase(
        id="array_dot_some_have_field",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"c": 2}]}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"c": 2}]}],
        msg="Dot notation through array matches when at least one element has field",
    ),
    QueryTestCase(
        id="deeply_nested_array_paths",
        filter={"a.b.c": {"$exists": True}},
        doc=[{"_id": 1, "a": [{"b": [{"c": 1}]}, {"b": [{"c": 2}]}]}],
        expected=[{"_id": 1, "a": [{"b": [{"c": 1}]}, {"b": [{"c": 2}]}]}],
        msg="Deeply nested array paths match",
    ),
    QueryTestCase(
        id="mixed_array_elements",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": [1, {"b": 2}, "str", None]}],
        expected=[{"_id": 1, "a": [1, {"b": 2}, "str", None]}],
        msg="Mixed array elements — matches when any element has field",
    ),
    QueryTestCase(
        id="array_null_element_has_field",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": [{"b": None}, {"c": 1}]}],
        expected=[{"_id": 1, "a": [{"b": None}, {"c": 1}]}],
        msg="Array element with null field still matches $exists: true",
    ),
    QueryTestCase(
        id="doubly_nested_array_no_traverse",
        filter={"a.b": {"$exists": False}},
        doc=[{"_id": 1, "a": [[{"b": 1}]]}],
        expected=[{"_id": 1, "a": [[{"b": 1}]]}],
        msg="$exists does not traverse into nested arrays within arrays",
    ),
    QueryTestCase(
        id="doubly_nested_array_true_no_traverse",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": [[{"b": 1}]]}],
        expected=[],
        msg="$exists true does not match through doubly nested arrays",
    ),
]

ARRAY_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="index_0_exists",
        filter={"a.0": {"$exists": True}},
        doc=[{"_id": 1, "a": [10, 20, 30]}],
        expected=[{"_id": 1, "a": [10, 20, 30]}],
        msg="Array index 0 exists",
    ),
    QueryTestCase(
        id="index_out_of_bounds",
        filter={"a.5": {"$exists": False}},
        doc=[{"_id": 1, "a": [10, 20, 30]}],
        expected=[{"_id": 1, "a": [10, 20, 30]}],
        msg="Array index out of bounds matches $exists: false",
    ),
    QueryTestCase(
        id="empty_array_index_0",
        filter={"a.0": {"$exists": False}},
        doc=[{"_id": 1, "a": []}],
        expected=[{"_id": 1, "a": []}],
        msg="Empty array index 0 matches $exists: false",
    ),
    QueryTestCase(
        id="very_large_index",
        filter={"a.999999": {"$exists": False}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="Very large array index matches $exists: false",
    ),
]

NUMERIC_KEY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="object_numeric_key",
        filter={"a.0": {"$exists": True}},
        doc=[{"_id": 1, "a": {"0": "value"}}],
        expected=[{"_id": 1, "a": {"0": "value"}}],
        msg="Numeric key on object matches",
    ),
]

SPECIAL_PATH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negative_array_index",
        filter={"a.-1": {"$exists": False}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="Negative array index matches $exists: false",
    ),
    QueryTestCase(
        id="double_dot_path",
        filter={"a..b": {"$exists": True}},
        doc=[{"_id": 1, "a": {"b": 1}}],
        expected=[],
        msg="Double dot in path does not match",
    ),
    QueryTestCase(
        id="leading_dot_path",
        filter={".a": {"$exists": True}},
        doc=[{"_id": 1, "a": 1}],
        expected=[],
        msg="Leading dot in path does not match",
    ),
    QueryTestCase(
        id="trailing_dot_path",
        filter={"a.": {"$exists": True}},
        doc=[{"_id": 1, "a": 1}],
        expected=[],
        msg="Trailing dot in path does not match",
    ),
    QueryTestCase(
        id="deeply_nested_array_false",
        filter={"a.b.c": {"$exists": False}},
        doc=[{"_id": 1, "a": [{"b": [{"d": 1}]}]}],
        expected=[{"_id": 1, "a": [{"b": [{"d": 1}]}]}],
        msg="Deeply nested array path matches $exists: false when field absent",
    ),
]

NON_OBJECT_TRAVERSAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="scalar_traversal_not_match",
        filter={"a.b": {"$exists": True}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="Cannot traverse scalar — $exists: true does not match",
    ),
    QueryTestCase(
        id="scalar_traversal_false_match",
        filter={"a.b": {"$exists": False}},
        doc=[{"_id": 1, "a": 5}],
        expected=[{"_id": 1, "a": 5}],
        msg="Cannot traverse scalar — $exists: false matches",
    ),
    QueryTestCase(
        id="null_traversal_false_match",
        filter={"a.b": {"$exists": False}},
        doc=[{"_id": 1, "a": None}],
        expected=[{"_id": 1, "a": None}],
        msg="Cannot traverse null — $exists: false matches",
    ),
    QueryTestCase(
        id="entire_path_missing",
        filter={"a.b.c": {"$exists": False}},
        doc=[{"_id": 1, "x": 1}],
        expected=[{"_id": 1, "x": 1}],
        msg="Entire path missing matches $exists: false",
    ),
]

ALL_TESTS = (
    SIMPLE_NESTED_TESTS
    + DEEP_NESTED_TESTS
    + ARRAY_PATH_TESTS
    + ARRAY_INDEX_TESTS
    + NUMERIC_KEY_TESTS
    + SPECIAL_PATH_TESTS
    + NON_OBJECT_TRAVERSAL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_exists_nested_field_paths(collection, test):
    """Parametrized test for $exists with nested field paths."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
