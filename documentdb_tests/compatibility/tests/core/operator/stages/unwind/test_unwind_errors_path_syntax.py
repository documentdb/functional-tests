"""Tests for $unwind stage — path syntax and shorthand equivalence errors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    OVERFLOW_ERROR,
    UNWIND_MISSING_PATH_ERROR,
    UNWIND_PATH_NO_DOLLAR_ERROR,
    UNWIND_PATH_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Shorthand Document Form Error Equivalence]: the shorthand and
# document forms produce identical error codes for invalid paths.
UNWIND_SHORTHAND_EQUIV_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equiv_error_shorthand_empty_string",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": ""}],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="Shorthand form should reject empty string path",
    ),
    StageTestCase(
        "equiv_error_document_form_empty_string",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": ""}}],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="Document form should reject empty string path with same error as shorthand",
    ),
    StageTestCase(
        "equiv_error_shorthand_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": "a"}],
        error_code=UNWIND_PATH_NO_DOLLAR_ERROR,
        msg="Shorthand form should reject path without dollar prefix",
    ),
    StageTestCase(
        "equiv_error_document_form_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "a"}}],
        error_code=UNWIND_PATH_NO_DOLLAR_ERROR,
        msg="Document form should reject path without dollar prefix with same error as shorthand",
    ),
    StageTestCase(
        "equiv_error_shorthand_bare_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": "$"}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="Shorthand form should reject bare dollar path",
    ),
    StageTestCase(
        "equiv_error_document_form_bare_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$"}}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="Document form should reject bare dollar path with same error as shorthand",
    ),
]

# Property [Path Field Path Syntax]: the path string must be a valid field
# path starting with '$', containing no empty components, no trailing dot, no
# null bytes, no '$' in non-initial components, no system variables, and no
# more than 200 path components.
UNWIND_PATH_FIELD_PATH_SYNTAX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "path_syntax_system_variable_root",
        docs=[],
        pipeline=[{"$unwind": {"path": "$$ROOT"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unwind should reject $$ROOT system variable as path",
    ),
    StageTestCase(
        "path_syntax_system_variable_current",
        docs=[],
        pipeline=[{"$unwind": {"path": "$$CURRENT"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unwind should reject $$CURRENT system variable as path",
    ),
    StageTestCase(
        "path_syntax_dollar_in_non_initial_component",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a.$b"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unwind should reject $ in a non-initial path component",
    ),
    StageTestCase(
        "path_syntax_empty_component_double_dot",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a..b"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unwind should reject empty path component from double dot",
    ),
    StageTestCase(
        "path_syntax_empty_component_leading_dot",
        docs=[],
        pipeline=[{"$unwind": {"path": "$.a"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unwind should reject empty path component from leading dot",
    ),
    StageTestCase(
        "path_syntax_trailing_dot",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a."}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$unwind should reject trailing dot in path",
    ),
    StageTestCase(
        "path_syntax_null_byte",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a\x00b"}}],
        error_code=EXPRESSION_FIELD_PATH_NULL_BYTE_ERROR,
        msg="$unwind should reject null byte in path",
    ),
    StageTestCase(
        "path_syntax_depth_201_exceeds_limit",
        docs=[],
        pipeline=[{"$unwind": {"path": "$" + ".".join(["a"] * 201)}}],
        error_code=OVERFLOW_ERROR,
        msg="$unwind should reject path with 201 components (exceeds 200 limit)",
    ),
]

# Property [Missing Path]: omitting the path field in document form produces
# a missing path error.
UNWIND_MISSING_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "missing_path_empty_document",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {}}],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="$unwind should reject document form with no path field",
    ),
    StageTestCase(
        "missing_path_only_options",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="$unwind should reject document form with options but no path field",
    ),
]

# Property [Expression Arguments Rejected]: path is a static field path
# string, not an expression - expression objects such as $literal are rejected
# as their literal BSON type (object).
UNWIND_EXPRESSION_ARGUMENTS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "expr_arg_path_literal",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": {"$literal": "$a"}}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path should reject $literal expression object as non-string type",
    ),
]

UNWIND_PATH_SYNTAX_ALL_TESTS = (
    UNWIND_SHORTHAND_EQUIV_ERROR_TESTS
    + UNWIND_PATH_FIELD_PATH_SYNTAX_TESTS
    + UNWIND_MISSING_PATH_TESTS
    + UNWIND_EXPRESSION_ARGUMENTS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_PATH_SYNTAX_ALL_TESTS))
def test_unwind_path_syntax_errors(collection, test_case: StageTestCase):
    """Test $unwind path syntax and shorthand equivalence errors."""
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
