"""
Tests for $regex query operator on nested and dotted field paths.

Covers $regex on nested objects, deeply nested paths, array indices,
type mismatches on dotted paths, arrays of subdocuments, and nested
arrays of strings.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NESTED_PATH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="dotted_path_deeply_nested",
        filter={"a.b.c.d": {"$regex": "test"}},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": "test"}}}},
            {"_id": 2, "a": {"b": {"c": {"d": "other"}}}},
        ],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": "test"}}}}],
        msg="$regex on deeply nested path a.b.c.d should match",
    ),
    QueryTestCase(
        id="dotted_path_array_index",
        filter={"a.0": {"$regex": "test"}},
        doc=[
            {"_id": 1, "a": ["test1", "test2"]},
            {"_id": 2, "a": ["other"]},
        ],
        expected=[{"_id": 1, "a": ["test1", "test2"]}],
        msg="$regex on array index a.0 should match first element",
    ),
    QueryTestCase(
        id="dotted_path_type_mismatch_no_error",
        filter={"a.b": {"$regex": "test"}},
        doc=[
            {"_id": 1, "a": "hello"},
            {"_id": 2, "a": {"b": "test"}},
        ],
        expected=[{"_id": 2, "a": {"b": "test"}}],
        msg="$regex on a.b where a is string should not match and not error",
    ),
    QueryTestCase(
        id="dotted_path_array_of_subdocs",
        filter={"a.b": {"$regex": "test"}},
        doc=[
            {"_id": 1, "a": [{"b": "test1"}, {"b": "other"}]},
            {"_id": 2, "a": [{"b": "other"}]},
        ],
        expected=[{"_id": 1, "a": [{"b": "test1"}, {"b": "other"}]}],
        msg="$regex on dotted path into array of subdocuments should match",
    ),
    QueryTestCase(
        id="dotted_path_nested_array_of_strings",
        filter={"a.b": {"$regex": "test"}},
        doc=[
            {"_id": 1, "a": {"b": ["test1", "other"]}},
            {"_id": 2, "a": {"b": ["other"]}},
        ],
        expected=[{"_id": 1, "a": {"b": ["test1", "other"]}}],
        msg="$regex on dotted path into nested array of strings should match",
    ),
]

ALL_TESTS = NESTED_PATH_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_regex_nested_paths(collection, test):
    """Parametrized test for $regex on nested and dotted field paths."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
