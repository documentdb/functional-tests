"""Tests for $project computed fields, $$REMOVE, and array literals."""

from __future__ import annotations

from typing import Any

import pytest
from bson.son import SON

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Computed / Expression Fields]: expressions, field path references,
# $literal, and special values produce computed field values in the output.
PROJECT_COMPUTED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "computed_field_path_ref",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"result": "$a"}}],
        expected=[{"_id": 1, "result": 10}],
        msg="$project should copy a field via field path reference",
    ),
    StageTestCase(
        "computed_literal_zero",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"flag": {"$literal": 0}}}],
        expected=[{"_id": 1, "flag": 0}],
        msg="$project $literal should prevent 0 from being interpreted as exclusion",
    ),
    StageTestCase(
        "computed_literal_true",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"flag": {"$literal": True}}}],
        expected=[{"_id": 1, "flag": True}],
        msg="$project $literal should prevent true from being interpreted as inclusion",
    ),
    StageTestCase(
        "computed_literal_false",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"flag": {"$literal": False}}}],
        expected=[{"_id": 1, "flag": False}],
        msg="$project $literal should prevent false from being interpreted as exclusion",
    ),
    StageTestCase(
        "computed_null_value",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": 1, "x": None}}],
        expected=[{"_id": 1, "a": 10, "x": None}],
        msg="$project should treat null as a computed expression setting the field to null",
    ),
    StageTestCase(
        "computed_missing_field_ref_omitted",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"result": MISSING}}],
        expected=[{"_id": 1}],
        msg="$project should omit a field when it references a missing field",
    ),
    StageTestCase(
        "computed_self_reference",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": "$a"}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project self-reference should read from the original document",
    ),
    StageTestCase(
        "computed_cross_reference",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", "$b"), ("b", "$a")])}],
        expected=[{"_id": 1, "a": 20, "b": 10}],
        msg=(
            "$project cross-reference should read from the original document,"
            " not intermediate projection state"
        ),
    ),
]

# Property [$$REMOVE Behavior]: $$REMOVE removes a field from output and
# interacts correctly with conditional expressions and inclusion mode.
PROJECT_REMOVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "remove_basic",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": 1, "b": "$$REMOVE"}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should remove a field when its value is $$REMOVE",
    ),
    StageTestCase(
        "remove_cond_true",
        docs=[{"_id": 1, "a": 10, "show": True}],
        pipeline=[
            {"$project": {"result": {"$cond": [{"$eq": ["$show", True]}, "$a", "$$REMOVE"]}}}
        ],
        expected=[{"_id": 1, "result": 10}],
        msg="$project $$REMOVE with $cond should keep field when condition is true",
    ),
    StageTestCase(
        "remove_cond_false",
        docs=[{"_id": 1, "a": 20, "show": False}],
        pipeline=[
            {"$project": {"result": {"$cond": [{"$eq": ["$show", True]}, "$a", "$$REMOVE"]}}}
        ],
        expected=[{"_id": 1}],
        msg="$project $$REMOVE with $cond should remove field when condition is false",
    ),
    StageTestCase(
        "remove_dotted_path",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": 1, "b": "$$REMOVE.x.y"}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project should remove a field when $$REMOVE has additional path components",
    ),
    StageTestCase(
        "remove_inside_array_becomes_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"arr": ["$a", "$$REMOVE", "hello"]}}],
        expected=[{"_id": 1, "arr": [10, None, "hello"]}],
        msg="$project $$REMOVE inside an array literal should become null",
    ),
    StageTestCase(
        "remove_compatible_with_inclusion",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[{"$project": {"a": 1, "b": "$$REMOVE", "c": 1}}],
        expected=[{"_id": 1, "a": 10, "c": 30}],
        msg=(
            "$project $$REMOVE should be compatible with inclusion mode"
            " without triggering the mixing restriction"
        ),
    ),
]

# Property [Array Literal Fields]: square bracket syntax creates new array
# fields from field references and literal values.
PROJECT_ARRAY_LITERAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        "array_literal_field_refs",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"arr": ["$a", "$b"]}}],
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="$project should create a new array field from field references",
    ),
    StageTestCase(
        "array_literal_missing_ref_becomes_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"arr": ["$a", MISSING]}}],
        expected=[{"_id": 1, "arr": [10, None]}],
        msg="$project should substitute null for missing field references inside array literals",
    ),
    StageTestCase(
        "array_literal_empty",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"arr": []}}],
        expected=[{"_id": 1, "arr": []}],
        msg="$project should treat an empty array as a computed field producing an empty array",
    ),
]

PROJECT_COMPUTED_ALL_TESTS = (
    PROJECT_COMPUTED_TESTS + PROJECT_REMOVE_TESTS + PROJECT_ARRAY_LITERAL_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PROJECT_COMPUTED_ALL_TESTS))
def test_project_computed(collection: Any, test_case: StageTestCase) -> None:
    """Test $project computed fields."""
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
