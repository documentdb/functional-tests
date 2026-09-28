"""Tests for $push core behavior.

Covers: basic append, missing field creation, array as value, empty operand,
dot notation/nested fields, multiple fields, large arrays, $sort without $each literal.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_BEHAVIOR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "append_to_existing_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": 4}},
        expected={"_id": 1, "arr": [1, 2, 3, 4]},
        msg="$push should append value to end of existing array",
    ),
    UpdateTestCase(
        "append_to_empty_array",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": "first"}},
        expected={"_id": 1, "arr": ["first"]},
        msg="$push on empty array should add as first element",
    ),
    UpdateTestCase(
        "missing_field_creates_array",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$push": {"arr": 42}},
        expected={"_id": 1, "x": 1, "arr": [42]},
        msg="$push on missing field should create array and preserve existing fields",
    ),
    UpdateTestCase(
        "array_value_appended_as_single_element",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": [3, 4]}},
        expected={"_id": 1, "arr": [1, 2, [3, 4]]},
        msg="$push with array value should append entire array as single element",
    ),
    UpdateTestCase(
        "nested_array_value",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": [[1, 2], [3, 4]]}},
        expected={"_id": 1, "arr": [[[1, 2], [3, 4]]]},
        msg="$push with nested array appends the whole nested array as one element",
    ),
    UpdateTestCase(
        "object_value",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": {"name": "test", "val": 99}}},
        expected={"_id": 1, "arr": [{"name": "test", "val": 99}]},
        msg="$push with object value should append object to array",
    ),
    UpdateTestCase(
        "duplicate_value_allowed",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": 2}},
        expected={"_id": 1, "arr": [1, 2, 3, 2]},
        msg="$push should allow duplicate values",
    ),
    UpdateTestCase(
        "empty_operand_noop",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="$push with empty operand {} is a no-op",
    ),
]


NESTED_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "dot_notation_nested_array",
        setup_docs=[{"_id": 1, "a": {"b": [1, 2]}}],
        query={"_id": 1},
        update={"$push": {"a.b": 3}},
        expected={"_id": 1, "a": {"b": [1, 2, 3]}},
        msg="$push on nested array using dot notation",
    ),
    UpdateTestCase(
        "dot_notation_deeply_nested",
        setup_docs=[{"_id": 1, "a": {"b": {"c": {"d": [10]}}}}],
        query={"_id": 1},
        update={"$push": {"a.b.c.d": 20}},
        expected={"_id": 1, "a": {"b": {"c": {"d": [10, 20]}}}},
        msg="$push on deeply nested array using dot notation",
    ),
    UpdateTestCase(
        "dot_notation_creates_nested_path",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$push": {"a.b": "val"}},
        expected={"_id": 1, "a": {"b": ["val"]}},
        msg="$push on missing nested field creates structure",
    ),
    UpdateTestCase(
        "array_within_embedded_doc",
        setup_docs=[{"_id": 1, "obj": {"items": ["x"]}}],
        query={"_id": 1},
        update={"$push": {"obj.items": "y"}},
        expected={"_id": 1, "obj": {"items": ["x", "y"]}},
        msg="$push on array within embedded document",
    ),
    UpdateTestCase(
        "numeric_index_path",
        setup_docs=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3]}]}],
        query={"_id": 1},
        update={"$push": {"a.0.b": 99}},
        expected={"_id": 1, "a": [{"b": [1, 2, 99]}, {"b": [3]}]},
        msg="$push on a.0.b where a is an array uses numeric index",
    ),
]


MULTIPLE_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "push_multiple_fields",
        setup_docs=[{"_id": 1, "a": [1], "b": [10]}],
        query={"_id": 1},
        update={"$push": {"a": 2, "b": 20}},
        expected={"_id": 1, "a": [1, 2], "b": [10, 20]},
        msg="$push on multiple array fields in single operation",
    ),
    UpdateTestCase(
        "push_multiple_fields_independent",
        setup_docs=[{"_id": 1, "x": ["a"], "y": [1], "z": [True]}],
        query={"_id": 1},
        update={"$push": {"x": "b", "y": 2, "z": False}},
        expected={"_id": 1, "x": ["a", "b"], "y": [1, 2], "z": [True, False]},
        msg="$push on multiple fields should process each independently",
    ),
    UpdateTestCase(
        "push_multiple_fields_with_modifiers",
        setup_docs=[{"_id": 1, "a": [3, 1, 2], "b": [10, 20, 30]}],
        query={"_id": 1},
        update={
            "$push": {
                "a": {"$each": [4], "$sort": 1},
                "b": {"$each": [0], "$position": 0},
            }
        },
        expected={"_id": 1, "a": [1, 2, 3, 4], "b": [0, 10, 20, 30]},
        msg="$push multiple fields each with their own modifiers",
    ),
]


LARGE_ARRAY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "push_to_large_array",
        setup_docs=[{"_id": 1, "arr": list(range(1000))}],
        query={"_id": 1},
        update={"$push": {"arr": 1000}},
        expected={"_id": 1, "arr": list(range(1001))},
        msg="$push should append to large array correctly",
    ),
]


MODIFIER_WITHOUT_EACH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "sort_without_each_pushes_literal",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$sort": 1}}},
        expected={"_id": 1, "arr": [3, 1, 2, {"$sort": 1}]},
        msg="$sort without $each pushes the object as literal value",
    ),
]


ALL_TESTS = (
    CORE_BEHAVIOR_TESTS
    + NESTED_FIELD_TESTS
    + MULTIPLE_FIELD_TESTS
    + LARGE_ARRAY_TESTS
    + MODIFIER_WITHOUT_EACH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_push_core(collection, test: UpdateTestCase):
    """Test $push core behavior produces expected document."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
