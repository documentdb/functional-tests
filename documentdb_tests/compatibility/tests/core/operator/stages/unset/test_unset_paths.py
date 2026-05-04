"""Tests for $unset stage path handling."""

from __future__ import annotations

from functools import reduce
from typing import Any, cast

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Dotted Path Removal]: dot notation removes a nested field within a
# subdocument leaving the parent intact, and traverses arrays to remove the
# specified field from every object element.
UNSET_DOTTED_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dotted_nested_field",
        docs=[{"_id": 1, "a": {"b": 10, "c": 20}}],
        pipeline=[{"$unset": "a.b"}],
        expected=[{"_id": 1, "a": {"c": 20}}],
        msg="$unset should remove a nested field via dot notation leaving siblings intact",
    ),
    StageTestCase(
        "dotted_array_traversal",
        docs=[{"_id": 1, "arr": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}],
        pipeline=[{"$unset": "arr.x"}],
        expected=[{"_id": 1, "arr": [{"y": 2}, {"y": 4}]}],
        msg=(
            "$unset should traverse arrays and remove the specified"
            " field from every object element"
        ),
    ),
    StageTestCase(
        "dotted_numeric_index_on_array_ignored",
        docs=[{"_id": 1, "arr": [10, 20, 30]}],
        pipeline=[{"$unset": "arr.0"}],
        expected=[{"_id": 1, "arr": [10, 20, 30]}],
        msg="$unset with numeric path component should not index into an array",
    ),
    StageTestCase(
        "dotted_numeric_index_on_object_array_ignored",
        docs=[{"_id": 1, "arr": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}],
        pipeline=[{"$unset": "arr.0"}],
        expected=[{"_id": 1, "arr": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}],
        msg="$unset with numeric path component should not index into an array of objects",
    ),
    StageTestCase(
        "dotted_numeric_then_subfield_on_array_ignored",
        docs=[{"_id": 1, "arr": [{"sub": 10, "other": 20}, {"sub": 30, "other": 40}]}],
        pipeline=[{"$unset": "arr.0.sub"}],
        expected=[{"_id": 1, "arr": [{"sub": 10, "other": 20}, {"sub": 30, "other": 40}]}],
        msg="$unset with numeric index then subfield should not modify array elements",
    ),
    StageTestCase(
        "dotted_numeric_key_in_subdocument",
        docs=[{"_id": 1, "val": {"0": "zero", "1": "one", "a": "alpha"}}],
        pipeline=[{"$unset": "val.0"}],
        expected=[{"_id": 1, "val": {"1": "one", "a": "alpha"}}],
        msg=(
            "$unset with numeric path component should remove a"
            " literal numeric key from a subdocument"
        ),
    ),
    StageTestCase(
        "dotted_through_null_parent",
        docs=[{"_id": 1, "a": None, "b": 10}],
        pipeline=[{"$unset": "a.x"}],
        expected=[{"_id": 1, "a": None, "b": 10}],
        msg="$unset with dot notation through a null parent should leave the document unchanged",
    ),
    StageTestCase(
        "dotted_through_missing_parent",
        docs=[{"_id": 1, "b": 10}],
        pipeline=[{"$unset": "a.x"}],
        expected=[{"_id": 1, "b": 10}],
        msg="$unset with dot notation through a missing parent should leave the document unchanged",
    ),
]

# Property [_id Interactions]: $unset treats _id like any other field,
# removing it or its sub-fields when explicitly specified.
UNSET_ID_INTERACTIONS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "id_remove_string_form",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "_id"}],
        expected=[{"a": 10}],
        msg="$unset should exclude _id from output when specified as a string",
    ),
    StageTestCase(
        "id_remove_array_form",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["_id"]}],
        expected=[{"a": 10}],
        msg="$unset should exclude _id from output when specified in an array",
    ),
    StageTestCase(
        "id_compound_remove_subfield",
        docs=[{"_id": {"x": 1, "y": 2}, "a": 10}],
        pipeline=[{"$unset": "_id.x"}],
        expected=[{"_id": {"y": 2}, "a": 10}],
        msg=(
            "$unset should preserve _id with only the targeted"
            " sub-field removed from a compound _id"
        ),
    ),
    StageTestCase(
        "id_compound_remove_all_subfields",
        docs=[{"_id": {"x": 1, "y": 2}, "a": 10}],
        pipeline=[{"$unset": ["_id.x", "_id.y"]}],
        expected=[{"_id": {}, "a": 10}],
        msg=(
            "$unset should leave _id as an empty document when all"
            " sub-fields of a compound _id are removed"
        ),
    ),
    StageTestCase(
        "id_only_document",
        docs=[{"_id": 1}],
        pipeline=[{"$unset": "_id"}],
        expected=[{}],
        msg=(
            "$unset should produce an empty document when removing"
            " _id from a document containing only _id"
        ),
    ),
]

# Property [Large Field Count]: $unset handles large numbers of fields in
# the array form.
UNSET_LARGE_FIELD_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "large_field_count_array_form",
        docs=[
            {"_id": 1, **{f"f{i}": i for i in range(10_000)}},
        ],
        pipeline=[{"$unset": [f"f{i}" for i in range(10_000)]}],
        expected=[{"_id": 1}],
        msg="$unset should handle a large number of fields in the array form",
    ),
]

# Property [Field Path Validation - Accepted Depth]: a dotted path with up
# to 200 components is accepted without error. Document nesting is capped at
# 180 levels, so actual removal is tested at that depth.
UNSET_FIELD_PATH_DEPTH_ACCEPTED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_path_depth_200_accepted",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ".".join(["a"] * 200)}],
        expected=[{"_id": 1, "a": 10}],
        msg="$unset should accept a dotted path with exactly 200 components",
    ),
    StageTestCase(
        "field_path_depth_180_removes_nested",
        docs=[
            {
                "_id": 1,
                **reduce(
                    lambda v, k: {k: v},
                    reversed(["a"] * 179),
                    cast(Any, {"a": 1, "b": 2}),
                ),
            },
        ],
        pipeline=[{"$unset": ".".join(["a"] * 180)}],
        expected=[
            {
                "_id": 1,
                **reduce(
                    lambda v, k: {k: v},
                    reversed(["a"] * 179),
                    cast(Any, {"b": 2}),
                ),
            },
        ],
        msg="$unset should remove a field at the maximum document nesting depth",
    ),
]

# Property [Path Collision Non-Errors]: distinct paths that share a common
# prefix or differ only in case or Unicode form do not collide.
UNSET_PATH_COLLISION_NON_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sibling_paths_no_collision",
        docs=[{"_id": 1, "a": {"b": 10, "c": 20, "d": 30}}],
        pipeline=[{"$unset": ["a.b", "a.c"]}],
        expected=[{"_id": 1, "a": {"d": 30}}],
        msg="$unset with sibling dotted paths should remove both fields without collision",
    ),
    StageTestCase(
        "case_different_no_collision",
        docs=[{"_id": 1, "A": 10, "a": 20, "b": 30}],
        pipeline=[{"$unset": ["A", "a"]}],
        expected=[{"_id": 1, "b": 30}],
        msg=(
            "$unset with case-different field names should not"
            " collide and both fields should be removed"
        ),
    ),
    StageTestCase(
        "unicode_precomposed_decomposed_no_collision",
        docs=[{"_id": 1, "\u00e9": 10, "e\u0301": 20, "x": 30}],
        pipeline=[{"$unset": ["\u00e9", "e\u0301"]}],
        expected=[{"_id": 1, "x": 30}],
        msg=(
            "$unset with precomposed and decomposed Unicode forms"
            " should not collide and both fields should be removed"
        ),
    ),
]

UNSET_PATH_TESTS = (
    UNSET_DOTTED_PATH_TESTS
    + UNSET_ID_INTERACTIONS_TESTS
    + UNSET_LARGE_FIELD_COUNT_TESTS
    + UNSET_FIELD_PATH_DEPTH_ACCEPTED_TESTS
    + UNSET_PATH_COLLISION_NON_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_PATH_TESTS))
def test_unset_paths(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset stage path handling."""
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
        ignore_doc_order=True,
    )
