"""Tests for $unset stage error precedence and validation timing."""

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
    UNSET_ARRAY_ELEMENT_TYPE_ERROR,
    UNSET_EMPTY_ARRAY_ERROR,
    UNSET_SPEC_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Error Precedence]: when multiple errors are present, the
# reported error follows a fixed precedence order.
UNSET_ERROR_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_type_over_null_byte",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [123, "a\x00b"]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="Type error should take precedence over null byte error",
    ),
    StageTestCase(
        "precedence_type_over_dollar_prefix",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [123, "$a"]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="Type error should take precedence over dollar prefix error",
    ),
    StageTestCase(
        "precedence_type_over_collision",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [123, "a", "a"]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="Type error should take precedence over path collision error",
    ),
    StageTestCase(
        "precedence_null_byte_over_dollar_prefix",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["a\x00b", "$a"]}],
        error_code=EMBEDDED_NULL_BYTE_ERROR,
        msg="Null byte error should take precedence over dollar prefix error",
    ),
    StageTestCase(
        "precedence_null_byte_over_collision",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["a\x00b", "a", "a"]}],
        error_code=EMBEDDED_NULL_BYTE_ERROR,
        msg="Null byte error should take precedence over path collision error",
    ),
    StageTestCase(
        "precedence_first_invalid_empty_before_dollar",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["", "$a"]}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="First invalid element determines error: empty string before dollar prefix",
    ),
    StageTestCase(
        "precedence_first_invalid_dollar_before_empty",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["$a", ""]}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="First invalid element determines error: dollar prefix before empty string",
    ),
    StageTestCase(
        "precedence_first_invalid_trailing_dot_before_empty",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["a.", ""]}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="First invalid element determines error: trailing dot before empty string",
    ),
    StageTestCase(
        "precedence_type_over_null_byte_reversed",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["a\x00b", 123]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="Type error should take precedence over null byte error regardless of position",
    ),
    StageTestCase(
        "precedence_null_byte_over_dollar_prefix_reversed",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["$a", "a\x00b"]}],
        error_code=EMBEDDED_NULL_BYTE_ERROR,
        msg=(
            "Null byte error should take precedence over"
            " dollar prefix error regardless of position"
        ),
    ),
    StageTestCase(
        "precedence_field_path_over_collision",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["$a", "b", "b"]}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="Field path validation error should take precedence over path collision error",
    ),
    StageTestCase(
        "precedence_first_invalid_empty_before_trailing_dot",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["", "a."]}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="First invalid element determines error: empty string before trailing dot",
    ),
]

# Property [Validation Independent of Collection State]: every validation
# error fires even on empty or non-existent collections.
UNSET_VALIDATION_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timing_spec_type_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": 123}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset spec type error should fire on empty collection",
    ),
    StageTestCase(
        "timing_array_element_type_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": [123]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array element type error should fire on empty collection",
    ),
    StageTestCase(
        "timing_empty_array_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": []}],
        error_code=UNSET_EMPTY_ARRAY_ERROR,
        msg="$unset empty array error should fire on empty collection",
    ),
    StageTestCase(
        "timing_field_path_empty_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": ""}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$unset empty field path error should fire on empty collection",
    ),
    StageTestCase(
        "timing_field_path_dollar_prefix_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": "$a"}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unset dollar prefix error should fire on empty collection",
    ),
    StageTestCase(
        "timing_field_path_empty_component_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": "a..b"}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unset empty component error should fire on empty collection",
    ),
    StageTestCase(
        "timing_field_path_trailing_dot_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": "a."}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$unset trailing dot error should fire on empty collection",
    ),
    StageTestCase(
        "timing_null_byte_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": "a\x00b"}],
        error_code=EMBEDDED_NULL_BYTE_ERROR,
        msg="$unset null byte error should fire on empty collection",
    ),
    StageTestCase(
        "timing_overflow_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": ".".join(["a"] * 201)}],
        error_code=OVERFLOW_ERROR,
        msg="$unset overflow error should fire on empty collection",
    ),
    StageTestCase(
        "timing_collision_child_after_parent_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": ["a", "a.b"]}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$unset child-after-parent collision error should fire on empty collection",
    ),
    StageTestCase(
        "timing_collision_parent_after_child_error_empty_collection",
        docs=[],
        pipeline=[{"$unset": ["a.b", "a"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$unset parent-after-child collision error should fire on empty collection",
    ),
]

# Property [Validation Independent of Nonexistent Collection]: every
# validation error fires even on a non-existent collection.
UNSET_VALIDATION_NONEXISTENT_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timing_spec_type_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": 123}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset spec type error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_array_element_type_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": [123]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array element type error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_empty_array_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": []}],
        error_code=UNSET_EMPTY_ARRAY_ERROR,
        msg="$unset empty array error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_field_path_empty_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": ""}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$unset empty field path error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_field_path_dollar_prefix_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": "$a"}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unset dollar prefix error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_field_path_empty_component_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": "a..b"}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unset empty component error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_field_path_trailing_dot_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": "a."}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$unset trailing dot error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_null_byte_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": "a\x00b"}],
        error_code=EMBEDDED_NULL_BYTE_ERROR,
        msg="$unset null byte error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_overflow_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": ".".join(["a"] * 201)}],
        error_code=OVERFLOW_ERROR,
        msg="$unset overflow error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_collision_child_after_parent_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": ["a", "a.b"]}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$unset child-after-parent collision error should fire on non-existent collection",
    ),
    StageTestCase(
        "timing_collision_parent_after_child_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$unset": ["a.b", "a"]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$unset parent-after-child collision error should fire on non-existent collection",
    ),
]

UNSET_ERROR_BEHAVIOR_TESTS = (
    UNSET_ERROR_PRECEDENCE_TESTS
    + UNSET_VALIDATION_EMPTY_COLLECTION_TESTS
    + UNSET_VALIDATION_NONEXISTENT_COLLECTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_ERROR_BEHAVIOR_TESTS))
def test_unset_error_behavior(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset stage error precedence and validation timing."""
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
