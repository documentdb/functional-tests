"""
Tests for $or with array and embedded document field lookups.

Tests dot notation, array element matching, and deeply nested paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_element_match",
        filter={"$or": [{"arr": 1}, {"arr": 2}]},
        doc=[
            {"_id": 1, "arr": [1, 3]},
            {"_id": 2, "arr": [2, 4]},
            {"_id": 3, "arr": [5, 6]},
        ],
        expected=[{"_id": 1, "arr": [1, 3]}, {"_id": 2, "arr": [2, 4]}],
        msg="$or matches docs where array contains either value",
    ),
    QueryTestCase(
        id="dot_notation_array_index",
        filter={"$or": [{"arr.0": 1}, {"arr.1": 2}]},
        doc=[
            {"_id": 1, "arr": [1, 9]},
            {"_id": 2, "arr": [9, 2]},
            {"_id": 3, "arr": [9, 9]},
        ],
        expected=[{"_id": 1, "arr": [1, 9]}, {"_id": 2, "arr": [9, 2]}],
        msg="$or with dot notation into array positions",
    ),
    QueryTestCase(
        id="dot_notation_embedded_doc",
        filter={"$or": [{"a.b": 1}, {"a.c": 2}]},
        doc=[
            {"_id": 1, "a": {"b": 1, "c": 9}},
            {"_id": 2, "a": {"b": 9, "c": 2}},
            {"_id": 3, "a": {"b": 9, "c": 9}},
        ],
        expected=[
            {"_id": 1, "a": {"b": 1, "c": 9}},
            {"_id": 2, "a": {"b": 9, "c": 2}},
        ],
        msg="$or with dot notation into embedded document",
    ),
    QueryTestCase(
        id="deeply_nested_paths",
        filter={"$or": [{"a.b.c": 1}, {"x.y.z": 2}]},
        doc=[
            {"_id": 1, "a": {"b": {"c": 1}}},
            {"_id": 2, "x": {"y": {"z": 2}}},
            {"_id": 3, "a": {"b": {"c": 9}}},
        ],
        expected=[
            {"_id": 1, "a": {"b": {"c": 1}}},
            {"_id": 2, "x": {"y": {"z": 2}}},
        ],
        msg="$or with deeply nested dot notation paths",
    ),
    QueryTestCase(
        id="array_of_objects_dot_notation",
        filter={"$or": [{"a.b": 1}, {"a.c": 2}]},
        doc=[
            {"_id": 1, "a": [{"b": 1}, {"c": 9}]},
            {"_id": 2, "a": [{"b": 9}, {"c": 2}]},
            {"_id": 3, "a": [{"b": 9}, {"c": 9}]},
        ],
        expected=[
            {"_id": 1, "a": [{"b": 1}, {"c": 9}]},
            {"_id": 2, "a": [{"b": 9}, {"c": 2}]},
        ],
        msg="$or with dot notation into array of objects",
    ),
    QueryTestCase(
        id="dot_notation_nested_array_index",
        filter={"$or": [{"a.0.0": 1}]},
        doc=[
            {"_id": 1, "a": [[1, 2], [3, 4]]},
            {"_id": 2, "a": [[5, 6], [7, 8]]},
        ],
        expected=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        msg="$or with dot notation into nested array (a.0.0) matches first sub-array element",
    ),
    QueryTestCase(
        id="missing_nested_field_no_match",
        filter={"$or": [{"x.y.z": 1}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "x": {"y": 2}}],
        expected=[],
        msg="$or with dot path that doesn't exist in any doc returns empty",
    ),
    QueryTestCase(
        id="dot_notation_into_null_intermediate",
        filter={"$or": [{"a.b": 1}]},
        doc=[
            {"_id": 1, "a": None},
            {"_id": 2, "a": 5},
            {"_id": 3, "a": {"b": 1}},
        ],
        expected=[{"_id": 3, "a": {"b": 1}}],
        msg="$or with dot notation where intermediate is null or scalar does not match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_or_field_lookup(collection, test):
    """Test $or with array and embedded document field lookups."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
