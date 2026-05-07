"""
Tests for $and with array and embedded document field lookups.

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
        id="array_contains_both",
        filter={"$and": [{"arr": 1}, {"arr": 2}]},
        doc=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1, 3]},
            {"_id": 3, "arr": [2, 3]},
        ],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$and matches docs where array contains both values",
    ),
    QueryTestCase(
        id="dot_notation_array_index",
        filter={"$and": [{"arr.0": 1}, {"arr.1": 2}]},
        doc=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [2, 1, 3]},
        ],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$and with dot notation into array positions",
    ),
    QueryTestCase(
        id="dot_notation_embedded_doc",
        filter={"$and": [{"a.b": 1}, {"a.c": 2}]},
        doc=[
            {"_id": 1, "a": {"b": 1, "c": 2}},
            {"_id": 2, "a": {"b": 1, "c": 3}},
        ],
        expected=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        msg="$and with dot notation into embedded document",
    ),
    QueryTestCase(
        id="deeply_nested_paths",
        filter={"$and": [{"a.b.c.d": 1}, {"x.y.z": 2}]},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": 1}}}, "x": {"y": {"z": 2}}},
            {"_id": 2, "a": {"b": {"c": {"d": 1}}}, "x": {"y": {"z": 3}}},
        ],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": 1}}}, "x": {"y": {"z": 2}}}],
        msg="$and with deeply nested dot notation paths",
    ),
    QueryTestCase(
        id="entire_embedded_document",
        filter={"$and": [{"a": {"b": 1, "c": 2}}, {"d": 3}]},
        doc=[
            {"_id": 1, "a": {"b": 1, "c": 2}, "d": 3},
            {"_id": 2, "a": {"b": 1, "c": 2}, "d": 4},
        ],
        expected=[{"_id": 1, "a": {"b": 1, "c": 2}, "d": 3}],
        msg="$and matching entire embedded document",
    ),
    QueryTestCase(
        id="array_of_objects_dot_notation",
        filter={"$and": [{"a.b": 1}, {"a.c": 2}]},
        doc=[
            {"_id": 1, "a": [{"b": 1, "c": 2}, {"b": 3, "c": 4}]},
            {"_id": 2, "a": [{"b": 1, "c": 4}, {"b": 3, "c": 2}]},
        ],
        expected=[
            {"_id": 1, "a": [{"b": 1, "c": 2}, {"b": 3, "c": 4}]},
            {"_id": 2, "a": [{"b": 1, "c": 4}, {"b": 3, "c": 2}]},
        ],
        msg="$and with dot notation into array of objects matches across elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_field_lookup(collection, test):
    """Test $and with array and embedded document field lookups."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
