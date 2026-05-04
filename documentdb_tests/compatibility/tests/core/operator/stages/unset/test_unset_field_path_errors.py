"""Tests for $unset stage field path validation errors."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EMBEDDED_NULL_BYTE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    OVERFLOW_ERROR,
    PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
    PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Path Validation Errors]: invalid field path syntax
# produces a specific validation error.
UNSET_FIELD_PATH_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_path_empty_string",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ""}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$unset with empty string should produce an empty field path error",
    ),
    StageTestCase(
        "field_path_dollar_prefix",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "$a"}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unset with $-prefixed field name should produce a dollar prefix error",
    ),
    StageTestCase(
        "field_path_bare_dollar",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "$"}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unset with bare $ should produce a dollar prefix error",
    ),
    StageTestCase(
        "field_path_double_dollar",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "$$"}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unset with $$ should produce a dollar prefix error",
    ),
    StageTestCase(
        "field_path_dollar_prefix_non_leading",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "a.$b"}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg=(
            "$unset with $-prefixed component at a non-leading"
            " position should produce a dollar prefix error"
        ),
    ),
    StageTestCase(
        "field_path_leading_dot",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ".a"}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unset with leading dot should produce an empty component error",
    ),
    StageTestCase(
        "field_path_double_dot",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "a..b"}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unset with double dot should produce an empty component error",
    ),
    StageTestCase(
        "field_path_trailing_dot",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "a."}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$unset with trailing dot should produce a trailing dot error",
    ),
    StageTestCase(
        "field_path_dollar_prefix_trailing_dot_precedence",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "$a."}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg=(
            "$unset with $-prefixed field and trailing dot should"
            " produce a trailing dot error (trailing dot takes precedence)"
        ),
    ),
    StageTestCase(
        "field_path_null_byte",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": "a\x00b"}],
        error_code=EMBEDDED_NULL_BYTE_ERROR,
        msg="$unset with null byte in field name should produce a null byte error",
    ),
    StageTestCase(
        "field_path_depth_exceeds_200",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ".".join(["a"] * 201)}],
        error_code=OVERFLOW_ERROR,
        msg="$unset with path depth exceeding 200 should produce an overflow error",
    ),
]

# Property [Path Collision Errors]: overlapping or duplicate paths in array
# mode produce a path collision error.
UNSET_PATH_COLLISION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "path_collision_duplicate_field",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["a", "a"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$unset with duplicate field name in array should produce a path collision error",
    ),
    StageTestCase(
        "path_collision_duplicate_dotted_path",
        docs=[{"_id": 1, "a": {"b": 10}}],
        pipeline=[{"$unset": ["a.b", "a.b"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$unset with duplicate dotted path should produce a path collision error",
    ),
    StageTestCase(
        "path_collision_duplicate_numeric_path",
        docs=[{"_id": 1, "a": {"0": 10}}],
        pipeline=[{"$unset": ["a.0", "a.0"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$unset with duplicate numeric dotted path should produce a path collision error",
    ),
    StageTestCase(
        "path_collision_duplicate_deep_path",
        docs=[{"_id": 1, "a": {"b": {"c": 10}}}],
        pipeline=[{"$unset": ["a.b.c", "a.b.c"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$unset with duplicate deep dotted path should produce a path collision error",
    ),
    StageTestCase(
        "path_collision_ancestor_before_descendant",
        docs=[{"_id": 1, "a": {"b": 10}}],
        pipeline=[{"$unset": ["a", "a.b"]}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$unset with ancestor path before descendant should produce a path collision error",
    ),
    StageTestCase(
        "path_collision_ancestor_before_deep_descendant",
        docs=[{"_id": 1, "a": {"b": {"c": 10}}}],
        pipeline=[{"$unset": ["a", "a.b.c"]}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg=(
            "$unset with ancestor path before deep descendant"
            " should produce a path collision error"
        ),
    ),
    StageTestCase(
        "path_collision_descendant_before_ancestor",
        docs=[{"_id": 1, "a": {"b": 10}}],
        pipeline=[{"$unset": ["a.b", "a"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$unset with descendant path before ancestor should produce a path collision error",
    ),
    StageTestCase(
        "path_collision_deep_descendant_before_ancestor",
        docs=[{"_id": 1, "a": {"b": {"c": 10}}}],
        pipeline=[{"$unset": ["a.b.c", "a"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg=(
            "$unset with deep descendant path before ancestor"
            " should produce a path collision error"
        ),
    ),
]

UNSET_FIELD_PATH_ERROR_TESTS = (
    UNSET_FIELD_PATH_VALIDATION_ERROR_TESTS + UNSET_PATH_COLLISION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_FIELD_PATH_ERROR_TESTS))
def test_unset_field_path_errors(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset stage field path validation errors."""
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
