"""Tests for $project accepted inputs."""

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

# Property [$meta in Projection]: $meta expressions are accepted in
# projection, with some meta types producing no visible field and $meta
# being the only expression form allowed in exclusion mode.
PROJECT_META_TESTS: list[StageTestCase] = [
    StageTestCase(
        "meta_randval_no_visible_field",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": 1, "rv": {"$meta": "randVal"}}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project $meta: 'randVal' should produce no visible field in output",
    ),
    StageTestCase(
        "meta_indexkey_no_visible_field",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": 1, "ik": {"$meta": "indexKey"}}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project $meta: 'indexKey' should produce no visible field in output",
    ),
    StageTestCase(
        "meta_searchscore_no_visible_field",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": 1, "ss": {"$meta": "searchScore"}}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project $meta: 'searchScore' should produce no visible field in output",
    ),
    StageTestCase(
        "meta_searchhighlights_no_visible_field",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": 1, "sh": {"$meta": "searchHighlights"}}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$project $meta: 'searchHighlights' should produce no visible field in output",
    ),
    StageTestCase(
        "meta_exclusion_mode_allowed",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": {"a": 0, "rv": {"$meta": "randVal"}}}],
        expected=[{"_id": 1, "b": 20}],
        msg=(
            "$project $meta should be allowed in exclusion mode"
            " without triggering mixing restriction"
        ),
    ),
]

# Property [Sub-Projection Behaviors]: sub-document notation in a projection
# applies inclusion, computed, and expression rules within the nested document.
PROJECT_SUB_PROJECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sub_proj_inclusion_and_computed",
        docs=[{"_id": 1, "a": {"x": 10, "y": 20, "z": 30}}],
        pipeline=[{"$project": {"a": {"x": 1, "computed": {"$add": [1, 2]}}}}],
        expected=[{"_id": 1, "a": {"x": 10, "computed": 3}}],
        msg=(
            "$project sub-projection should support a mix of inclusion"
            " and computed fields within the nested document"
        ),
    ),
    StageTestCase(
        "sub_proj_literal_is_expression",
        docs=[{"_id": 1, "a": {"x": 10, "y": 20}}],
        pipeline=[{"$project": {"a": {"$literal": 1}}}],
        expected=[{"_id": 1, "a": 1}],
        msg=(
            "$project $literal in a sub-document should be treated as an"
            " expression, not as a sub-projection"
        ),
    ),
    StageTestCase(
        "sub_proj_scalar_field_omitted",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"a": {"x": 1}}}],
        expected=[{"_id": 1}],
        msg="$project sub-projection on a scalar field should omit the field from output",
    ),
]

# Property [Non-Existent Collection]: projecting from a collection that does
# not exist returns an empty result set without error.
PROJECT_NONEXISTENT_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nonexistent_collection_inclusion",
        docs=None,
        pipeline=[{"$project": {"a": 1}}],
        expected=[],
        msg="$project inclusion on a non-existent collection should return empty result",
    ),
    StageTestCase(
        "nonexistent_collection_exclusion",
        docs=None,
        pipeline=[{"$project": {"a": 0}}],
        expected=[],
        msg="$project exclusion on a non-existent collection should return empty result",
    ),
    StageTestCase(
        "nonexistent_collection_computed",
        docs=None,
        pipeline=[{"$project": {"r": {"$add": [1, 2]}}}],
        expected=[],
        msg="$project computed field on a non-existent collection should return empty result",
    ),
]

# Property [Empty Collection]: projecting from a collection with no documents
# returns an empty result set without error.
PROJECT_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection_inclusion",
        docs=[],
        pipeline=[{"$project": {"a": 1}}],
        expected=[],
        msg="$project inclusion on an empty collection should return empty result",
    ),
    StageTestCase(
        "empty_collection_exclusion",
        docs=[],
        pipeline=[{"$project": {"a": 0}}],
        expected=[],
        msg="$project exclusion on an empty collection should return empty result",
    ),
    StageTestCase(
        "empty_collection_computed",
        docs=[],
        pipeline=[{"$project": {"r": {"$add": [1, 2]}}}],
        expected=[],
        msg="$project computed field on an empty collection should return empty result",
    ),
]

# Property [Path Collision Non-Errors]: sibling paths and equivalent dotted
# and nested paths do not produce path collision errors.
PROJECT_PATH_COLLISION_NON_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "collision_sibling_paths_no_error",
        docs=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        pipeline=[{"$project": {"a.b": 1, "a.c": 1}}],
        expected=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        msg="$project should allow sibling paths without collision",
    ),
    StageTestCase(
        "collision_nested_equivalent_no_error",
        docs=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        pipeline=[{"$project": {"a": {"b": 1}, "a.c": 1}}],
        expected=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        msg="$project should merge dotted and nested equivalent paths without collision",
    ),
]

# Property [Field Name Acceptance]: field names with non-leading dollar signs,
# spaces, numeric names, and Unicode characters are accepted.
PROJECT_FIELD_NAME_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_name_non_leading_dollar",
        docs=[{"_id": 1, "a$bc": 10, "d": 20}],
        pipeline=[{"$project": {"a$bc": 1}}],
        expected=[{"_id": 1, "a$bc": 10}],
        msg="$project should accept non-leading $ in field names",
    ),
    StageTestCase(
        "field_name_space",
        docs=[{"_id": 1, "field name": 10, "d": 20}],
        pipeline=[{"$project": {"field name": 1}}],
        expected=[{"_id": 1, "field name": 10}],
        msg="$project should accept spaces in field names",
    ),
    StageTestCase(
        "field_name_numeric",
        docs=[{"_id": 1, "123": 10, "d": 20}],
        pipeline=[{"$project": {"123": 1}}],
        expected=[{"_id": 1, "123": 10}],
        msg="$project should accept numeric field names",
    ),
    StageTestCase(
        "field_name_unicode",
        docs=[{"_id": 1, "caf\u00e9": 10, "d": 20}],
        pipeline=[{"$project": {"caf\u00e9": 1}}],
        expected=[{"_id": 1, "caf\u00e9": 10}],
        msg="$project should accept Unicode characters in field names",
    ),
]

# Property [Large Projections]: projections with a large number of fields
# succeed for both inclusion and exclusion modes.
PROJECT_LARGE_PROJECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "large_inclusion_500_fields",
        docs=[{"_id": 1, **{f"f{i}": i for i in range(500)}}],
        pipeline=[{"$project": {f"f{i}": 1 for i in range(500)}}],
        expected=[{"_id": 1, **{f"f{i}": i for i in range(500)}}],
        msg="$project should succeed with 500 included fields",
    ),
    StageTestCase(
        "large_exclusion_500_fields",
        docs=[{"_id": 1, **{f"f{i}": i for i in range(500)}}],
        pipeline=[{"$project": {f"f{i}": 0 for i in range(500)}}],
        expected=[{"_id": 1}],
        msg="$project should succeed with 500 excluded fields",
    ),
]

# Property [Pipeline Semantics]: consecutive $project stages compose
# correctly, narrowing fields progressively.
PROJECT_PIPELINE_SEMANTICS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_consecutive_project",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        pipeline=[
            {"$project": {"a": 1, "b": 1}},
            {"$project": {"a": 1}},
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$project consecutive stages should narrow fields progressively",
    ),
]

PROJECT_ACCEPTANCE_TESTS = (
    PROJECT_META_TESTS
    + PROJECT_SUB_PROJECTION_TESTS
    + PROJECT_NONEXISTENT_COLLECTION_TESTS
    + PROJECT_EMPTY_COLLECTION_TESTS
    + PROJECT_PATH_COLLISION_NON_ERROR_TESTS
    + PROJECT_FIELD_NAME_ACCEPTANCE_TESTS
    + PROJECT_LARGE_PROJECTION_TESTS
    + PROJECT_PIPELINE_SEMANTICS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PROJECT_ACCEPTANCE_TESTS))
def test_project_acceptance(collection: Any, test_case: StageTestCase) -> None:
    """Test $project accepted inputs."""
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
