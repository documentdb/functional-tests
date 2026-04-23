"""Tests for $project _id field behavior."""

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

# Property [_id Field Behavior]: _id has special projection rules for
# suppression, mode determination, and sub-field projection.
PROJECT_ID_BEHAVIOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "id_suppress_in_inclusion_mode",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"_id": 0, "a": 1}}],
        expected=[{"a": 10}],
        msg="$project should suppress _id from output when _id: 0 in inclusion mode",
    ),
    StageTestCase(
        "id_explicit_in_exclusion_mode",
        docs=[{"_id": 42, "a": 10, "b": 20}],
        pipeline=[{"$project": {"_id": 1, "a": 0}}],
        expected=[{"_id": 42, "b": 20}],
        msg="$project should allow explicit _id: 1 in exclusion mode",
    ),
    StageTestCase(
        "id_null_computed",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"_id": None, "a": 1}}],
        expected=[{"a": 10, "_id": None}],
        msg="$project should treat _id: null as a computed expression setting _id to null",
    ),
    StageTestCase(
        "id_remove_alone_produces_empty",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"_id": "$$REMOVE"}}],
        expected=[{}],
        msg="$project with only _id: $$REMOVE should produce an empty document",
    ),
    StageTestCase(
        "id_subfield_inclusion",
        docs=[{"_id": {"x": 1, "y": 2}, "a": 10}],
        pipeline=[{"$project": {"_id.x": 1, "a": 1}}],
        expected=[{"_id": {"x": 1}, "a": 10}],
        msg="$project should project _id sub-fields via dotted path inclusion",
    ),
    StageTestCase(
        "id_subfield_exclusion",
        docs=[{"_id": {"x": 1, "y": 2}, "a": 10}],
        pipeline=[{"$project": {"_id.x": 0}}],
        expected=[{"_id": {"y": 2}, "a": 10}],
        msg="$project should exclude _id sub-fields via dotted path exclusion",
    ),
    StageTestCase(
        "id_zero_alone_exclusion_mode",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"_id": 0}}],
        expected=[{"a": 10, "b": 20}],
        msg="$project with only _id: 0 should be exclusion mode returning all other fields",
    ),
    StageTestCase(
        "id_one_alone_inclusion_mode",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"_id": 1}}],
        expected=[{"_id": 1}],
        msg="$project with only _id: 1 should be inclusion mode returning only _id",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(PROJECT_ID_BEHAVIOR_TESTS))
def test_project_id(collection: Any, test_case: StageTestCase) -> None:
    """Test $project _id field behavior."""
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
