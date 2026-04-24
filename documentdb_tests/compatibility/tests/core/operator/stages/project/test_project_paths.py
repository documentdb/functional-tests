"""Tests for $project dotted paths, array traversal, and numeric path components."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Dotted Path and Embedded Document Projection]: nested fields
# can be included, excluded, or computed via dotted paths and sub-document
# notation, with correct traversal through arrays and scalar parents.
PROJECT_DOTTED_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dotted_inclusion_nested",
        docs=[{"_id": 1, "a": {"b": 10, "c": 20}, "d": 30}],
        pipeline=[{"$project": {"a.b": 1}}],
        expected=[{"_id": 1, "a": {"b": 10}}],
        msg="$project should include a nested field via dotted path",
    ),
    StageTestCase(
        "dotted_exclusion_nested",
        docs=[{"_id": 1, "a": {"b": 10, "c": 20}, "d": 30}],
        pipeline=[{"$project": {"a.b": 0}}],
        expected=[{"_id": 1, "a": {"c": 20}, "d": 30}],
        msg="$project should exclude a nested field via dotted path",
    ),
    StageTestCase(
        "dotted_subdoc_inclusion_equivalent",
        docs=[{"_id": 1, "a": {"b": 10, "c": 20}, "d": 30}],
        pipeline=[{"$project": {"a": {"b": 1}}}],
        expected=[{"_id": 1, "a": {"b": 10}}],
        msg="$project sub-document notation should be equivalent to dotted path inclusion",
    ),
    StageTestCase(
        "dotted_subdoc_exclusion_equivalent",
        docs=[{"_id": 1, "a": {"b": 10, "c": 20}, "d": 30}],
        pipeline=[{"$project": {"a": {"b": 0}}}],
        expected=[{"_id": 1, "a": {"c": 20}, "d": 30}],
        msg="$project sub-document notation should be equivalent to dotted path exclusion",
    ),
    StageTestCase(
        "dotted_through_array_inclusion",
        docs=[{"_id": 1, "a": [{"b": 1, "c": 10}, {"b": 2, "c": 20}, {"b": 3, "c": 30}]}],
        pipeline=[{"$project": {"a.b": 1}}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}, {"b": 3}]}],
        msg="$project dotted path should traverse into array elements for inclusion",
    ),
    StageTestCase(
        "dotted_through_array_exclusion",
        docs=[{"_id": 1, "a": [{"b": 1, "c": 10}, {"b": 2, "c": 20}]}],
        pipeline=[{"$project": {"a.b": 0}}],
        expected=[{"_id": 1, "a": [{"c": 10}, {"c": 20}]}],
        msg="$project dotted path should traverse into array elements for exclusion",
    ),
    StageTestCase(
        "dotted_deep_nested_inclusion",
        docs=[{"_id": 1, "a": {"b": {"c": {"d": 42}}}}],
        pipeline=[{"$project": {"a.b.c.d": 1}}],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": 42}}}}],
        msg="$project should handle deeply nested dotted paths (3+ levels) for inclusion",
    ),
    StageTestCase(
        "dotted_deep_nested_exclusion",
        docs=[{"_id": 1, "a": {"b": {"c": {"d": 42, "e": 99}}}}],
        pipeline=[{"$project": {"a.b.c.d": 0}}],
        expected=[{"_id": 1, "a": {"b": {"c": {"e": 99}}}}],
        msg="$project should handle deeply nested dotted paths (3+ levels) for exclusion",
    ),
    StageTestCase(
        "dotted_key_in_subdoc",
        docs=[{"_id": 1, "a": {"b": {"c": 10}, "d": 20}}],
        pipeline=[{"$project": {"a": {"b.c": 1}}}],
        expected=[{"_id": 1, "a": {"b": {"c": 10}}}],
        msg="$project should support dotted key names inside sub-document notation",
    ),
    StageTestCase(
        "dotted_scalar_parent_inclusion_omits",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"a.b": 1}}],
        expected=[{"_id": 1}],
        msg=(
            "$project inclusion via dotted path should omit the field"
            " when the parent is a scalar"
        ),
    ),
    StageTestCase(
        "dotted_scalar_parent_exclusion_preserves",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"a.b": 0}}],
        expected=[{"_id": 1, "a": 42}],
        msg=(
            "$project exclusion via dotted path should preserve the scalar"
            " when the parent is a scalar"
        ),
    ),
    StageTestCase(
        "dotted_scalar_parent_computed_replaces",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"a.b": {"$literal": 99}}}],
        expected=[{"_id": 1, "a": {"b": 99}}],
        msg=(
            "$project computed via dotted path should replace the scalar"
            " with an object containing the computed field"
        ),
    ),
]

# Property [Array Traversal]: dotted path projection through arrays
# filters, preserves, or transforms array elements depending on the
# projection mode.
PROJECT_ARRAY_TRAVERSAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        "array_traversal_inclusion_removes_scalars_and_nulls",
        docs=[{"_id": 1, "a": [{"b": 1, "c": 10}, "scalar", None, {"b": 2, "c": 20}]}],
        pipeline=[{"$project": {"a.b": 1}}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg=(
            "$project inclusion through arrays should remove scalars and"
            " nulls and extract matching fields from objects"
        ),
    ),
    StageTestCase(
        "array_traversal_exclusion_preserves_scalars_and_nulls",
        docs=[{"_id": 1, "a": [{"b": 1, "c": 10}, "scalar", None, {"b": 2, "c": 20}]}],
        pipeline=[{"$project": {"a.b": 0}}],
        expected=[{"_id": 1, "a": [{"c": 10}, "scalar", None, {"c": 20}]}],
        msg=(
            "$project exclusion through arrays should preserve scalars"
            " and nulls and remove matching fields from objects"
        ),
    ),
    StageTestCase(
        "array_traversal_computed_overwrites",
        docs=[{"_id": 1, "a": [{"b": 1, "c": 10}, "scalar", None, {"b": 2, "c": 20}]}],
        pipeline=[{"$project": {"a.b": {"$literal": 99}}}],
        expected=[{"_id": 1, "a": [{"b": 99}, {"b": 99}, {"b": 99}, {"b": 99}]}],
        msg=(
            "$project computed through arrays should overwrite the field"
            " in objects, turn scalars into objects, and turn nulls into"
            " objects with the computed field"
        ),
    ),
    StageTestCase(
        "array_traversal_nested_arrays_inclusion",
        docs=[{"_id": 1, "a": [[{"b": 1, "c": 10}, {"b": 2, "c": 20}], [{"b": 3, "c": 30}]]}],
        pipeline=[{"$project": {"a.b": 1}}],
        expected=[{"_id": 1, "a": [[{"b": 1}, {"b": 2}], [{"b": 3}]]}],
        msg="$project inclusion should traverse nested arrays",
    ),
    StageTestCase(
        "array_traversal_nested_arrays_exclusion",
        docs=[{"_id": 1, "a": [[{"b": 1, "c": 10}, {"b": 2, "c": 20}], [{"b": 3, "c": 30}]]}],
        pipeline=[{"$project": {"a.b": 0}}],
        expected=[{"_id": 1, "a": [[{"c": 10}, {"c": 20}], [{"c": 30}]]}],
        msg="$project exclusion should traverse nested arrays",
    ),
    StageTestCase(
        "array_traversal_nested_arrays_computed",
        docs=[{"_id": 1, "a": [[{"b": 1}, {"b": 2}], [{"b": 3}]]}],
        pipeline=[{"$project": {"a.b": {"$literal": 99}}}],
        expected=[{"_id": 1, "a": [[{"b": 99}, {"b": 99}], [{"b": 99}]]}],
        msg="$project computed should traverse nested arrays",
    ),
    StageTestCase(
        "array_traversal_empty_array_inclusion",
        docs=[{"_id": 1, "a": []}],
        pipeline=[{"$project": {"a.b": 1}}],
        expected=[{"_id": 1, "a": []}],
        msg="$project inclusion should preserve an empty array as-is",
    ),
    StageTestCase(
        "array_traversal_empty_array_exclusion",
        docs=[{"_id": 1, "a": []}],
        pipeline=[{"$project": {"a.b": 0}}],
        expected=[{"_id": 1, "a": []}],
        msg="$project exclusion should preserve an empty array as-is",
    ),
    StageTestCase(
        "array_traversal_empty_array_computed",
        docs=[{"_id": 1, "a": []}],
        pipeline=[{"$project": {"a.b": {"$literal": 99}}}],
        expected=[{"_id": 1, "a": []}],
        msg="$project computed should preserve an empty array as-is",
    ),
    StageTestCase(
        "array_traversal_nested_empty_array_inclusion",
        docs=[{"_id": 1, "a": [[]]}],
        pipeline=[{"$project": {"a.b": 1}}],
        expected=[{"_id": 1, "a": [[]]}],
        msg="$project inclusion should preserve a nested empty array structure",
    ),
    StageTestCase(
        "array_traversal_nested_empty_array_exclusion",
        docs=[{"_id": 1, "a": [[]]}],
        pipeline=[{"$project": {"a.b": 0}}],
        expected=[{"_id": 1, "a": [[]]}],
        msg="$project exclusion should preserve a nested empty array structure",
    ),
    StageTestCase(
        "array_traversal_nested_empty_array_computed",
        docs=[{"_id": 1, "a": [[]]}],
        pipeline=[{"$project": {"a.b": {"$literal": 99}}}],
        expected=[{"_id": 1, "a": [[]]}],
        msg="$project computed should preserve a nested empty array structure",
    ),
]

# Property [Numeric Path Components]: numeric path components are treated
# as object key names, not array indices.
PROJECT_NUMERIC_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "numeric_path_inclusion_array_returns_empty",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"a.0": 1}}],
        expected=[{"_id": 1, "a": []}],
        msg=(
            "$project inclusion with numeric path component on an array"
            " should return an empty array, not the element at that index"
        ),
    ),
    StageTestCase(
        "numeric_path_exclusion_array_preserves",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"a.0": 0}}],
        expected=[{"_id": 1, "a": [10, 20, 30]}],
        msg=(
            "$project exclusion with numeric path component on an array"
            " should preserve the array as-is"
        ),
    ),
    StageTestCase(
        "numeric_path_computed_array_creates_objects",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"a.0": {"$literal": 99}}}],
        expected=[{"_id": 1, "a": [{"0": 99}, {"0": 99}, {"0": 99}]}],
        msg=(
            "$project computed with numeric path component on an array"
            " should create objects with the numeric key in each element"
        ),
    ),
    StageTestCase(
        "numeric_path_field_ref_array_returns_empty",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"result": "$a.0"}}],
        expected=[{"_id": 1, "result": []}],
        msg=(
            "$project field path reference with numeric component on an"
            " array should return an empty array, not the indexed element"
        ),
    ),
    StageTestCase(
        "numeric_path_inclusion_object_with_numeric_key",
        docs=[{"_id": 1, "a": {"0": "zero", "1": "one", "x": "other"}}],
        pipeline=[{"$project": {"a.0": 1}}],
        expected=[{"_id": 1, "a": {"0": "zero"}}],
        msg=(
            "$project inclusion with numeric path component on an object"
            " should match the literal key name"
        ),
    ),
    StageTestCase(
        "numeric_path_field_ref_object_with_numeric_key",
        docs=[{"_id": 1, "a": {"0": "zero", "1": "one"}}],
        pipeline=[{"$project": {"result": "$a.0"}}],
        expected=[{"_id": 1, "result": "zero"}],
        msg=(
            "$project field path reference with numeric component on an"
            " object should return the value at the literal key name"
        ),
    ),
]

PROJECT_PATH_TESTS = (
    PROJECT_DOTTED_PATH_TESTS + PROJECT_ARRAY_TRAVERSAL_TESTS + PROJECT_NUMERIC_PATH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PROJECT_PATH_TESTS))
def test_project_paths(collection: Any, test_case: StageTestCase) -> None:
    """Test $project path resolution."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
