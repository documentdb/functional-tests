"""
Tests for $set update operator - field path handling.

Covers dot notation for embedded documents, array elements, numeric field names,
and null/missing field handling.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TOP_LEVEL_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="update_existing_field",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"a": 99}},
        expected=[{"_id": 1, "a": 99}],
        msg="Should update existing top-level field",
    ),
    UpdateTestCase(
        id="create_new_field",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"b": 2}},
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="Should create non-existent top-level field",
    ),
]


DOT_NOTATION_EMBEDDED_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="update_nested_field",
        setup_docs=[{"_id": 1, "a": {"b": 1}}],
        query={"_id": 1},
        update={"$set": {"a.b": 99}},
        expected=[{"_id": 1, "a": {"b": 99}}],
        msg="Should update nested field via dot notation",
    ),
    UpdateTestCase(
        id="create_field_in_empty_embedded",
        setup_docs=[{"_id": 1, "a": {}}],
        query={"_id": 1},
        update={"$set": {"a.b": 2}},
        expected=[{"_id": 1, "a": {"b": 2}}],
        msg="Should create field in empty embedded document",
    ),
    UpdateTestCase(
        id="create_embedded_path_from_scratch",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"a.b": 1}},
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="Should create embedded document path when none exists",
    ),
    UpdateTestCase(
        id="create_deep_nested_path",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"a.b.c.d": 1}},
        expected=[{"_id": 1, "a": {"b": {"c": {"d": 1}}}}],
        msg="Should create deeply nested path",
    ),
]


DOT_NOTATION_ARRAY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="update_first_array_element",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.0": 99}},
        expected=[{"_id": 1, "arr": [99, 2, 3]}],
        msg="Should update first array element",
    ),
    UpdateTestCase(
        id="update_embedded_field_in_array",
        setup_docs=[{"_id": 1, "arr": [{"field": 1}, {"field": 2}]}],
        query={"_id": 1},
        update={"$set": {"arr.1.field": 99}},
        expected=[{"_id": 1, "arr": [{"field": 1}, {"field": 99}]}],
        msg="Should update embedded field in array element",
    ),
    UpdateTestCase(
        id="extend_array_by_one",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.3": 4}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        msg="Should extend array by one element",
    ),
    UpdateTestCase(
        id="extend_array_with_null_padding",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.5": 99}},
        expected=[{"_id": 1, "arr": [1, 2, 3, None, None, 99]}],
        msg="Should pad array with nulls when setting beyond length",
    ),
    UpdateTestCase(
        id="create_array_from_nonexistent_field",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"arr.0": "first"}},
        expected=[{"_id": 1, "arr": {"0": "first"}}],
        msg="Creates object not array — numeric keys are array indices only when parent is array",
    ),
    UpdateTestCase(
        id="dollar_prefix_in_nested_path",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"a.$bad": 1}},
        expected=[{"_id": 1, "a": {"$bad": 1}}],
        msg="Dollar-prefix allowed in nested field names",
    ),
]


NUMERIC_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="numeric_field_on_object",
        setup_docs=[{"_id": 1, "a": {"0": "old"}}],
        query={"_id": 1},
        update={"$set": {"a.0": "new"}},
        expected=[{"_id": 1, "a": {"0": "new"}}],
        msg="Should update object field '0' when parent is object",
    ),
    UpdateTestCase(
        id="numeric_index_on_array",
        setup_docs=[{"_id": 1, "a": ["x", "y", "z"]}],
        query={"_id": 1},
        update={"$set": {"a.0": "new"}},
        expected=[{"_id": 1, "a": ["new", "y", "z"]}],
        msg="Should update array element at index 0 when parent is array",
    ),
]


NULL_MISSING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="set_to_null",
        setup_docs=[{"_id": 1, "field": "value"}],
        query={"_id": 1},
        update={"$set": {"field": None}},
        expected=[{"_id": 1, "field": None}],
        msg="Should set field to null (field exists with null value)",
    ),
]

ALL_FIELD_PATH_TESTS = (
    TOP_LEVEL_TESTS
    + DOT_NOTATION_EMBEDDED_TESTS
    + DOT_NOTATION_ARRAY_TESTS
    + NUMERIC_FIELD_TESTS
    + NULL_MISSING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_FIELD_PATH_TESTS))
def test_set_field_paths(collection, test):
    """Test $set field path handling."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)
