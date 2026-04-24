"""Tests for $project error cases."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from bson.son import SON

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    OVERFLOW_ERROR,
    PROJECT_EMPTY_SPEC_ERROR,
    PROJECT_EMPTY_SUB_PROJECTION_ERROR,
    PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
    PROJECT_INCLUSION_IN_EXCLUSION_ERROR,
    PROJECT_OPERATOR_IN_EXCLUSION_ERROR,
    PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
    PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
    PROJECT_SPEC_NOT_OBJECT_ERROR,
    PROJECT_UNKNOWN_EXPRESSION_ERROR,
    PROJECT_VALUE_IN_EXCLUSION_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Mixing Restriction Errors]: combining inclusion and exclusion
# flags, or exclusion with expressions, in the same projection produces an
# error.
# Note: SON is used instead of plain dicts to make key order explicit, since
# the specific error code depends on which field the server encounters first.
PROJECT_MIXING_RESTRICTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "mixing_exclusion_after_inclusion",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 1), ("b", 0)])}],
        error_code=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="$project should reject exclusion on a non-_id field in inclusion projection",
    ),
    StageTestCase(
        "mixing_inclusion_after_exclusion",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 0), ("b", 1)])}],
        error_code=PROJECT_INCLUSION_IN_EXCLUSION_ERROR,
        msg="$project should reject inclusion on a field in exclusion projection",
    ),
    StageTestCase(
        "mixing_exclusion_with_expression",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 0), ("b", {"$add": [1, 2]})])}],
        error_code=PROJECT_OPERATOR_IN_EXCLUSION_ERROR,
        msg="$project should reject expression other than $meta in exclusion projection",
    ),
    StageTestCase(
        "mixing_exclusion_with_field_path",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 0), ("b", "$a")])}],
        error_code=PROJECT_VALUE_IN_EXCLUSION_ERROR,
        msg="$project should reject field path reference in exclusion projection",
    ),
    StageTestCase(
        "mixing_exclusion_with_null",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 0), ("b", None)])}],
        error_code=PROJECT_VALUE_IN_EXCLUSION_ERROR,
        msg="$project should reject null computed value in exclusion projection",
    ),
    StageTestCase(
        "mixing_exclusion_with_array_literal",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 0), ("b", ["$a"])])}],
        error_code=PROJECT_VALUE_IN_EXCLUSION_ERROR,
        msg="$project should reject array literal in exclusion projection",
    ),
    StageTestCase(
        "mixing_exclusion_with_remove",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 0), ("b", "$$REMOVE")])}],
        error_code=PROJECT_VALUE_IN_EXCLUSION_ERROR,
        msg="$project should reject $$REMOVE in exclusion projection",
    ),
    StageTestCase(
        "mixing_id_inclusion_exclusion_expression",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("_id", 1), ("a", 0), ("b", {"$add": [1, 2]})])}],
        error_code=PROJECT_OPERATOR_IN_EXCLUSION_ERROR,
        msg="$project should reject expression in exclusion mode even with _id: 1",
    ),
    StageTestCase(
        "mixing_id_expression_with_exclusion",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("_id", {"$add": [1, 2]}), ("a", 0)])}],
        error_code=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="$project should reject exclusion when _id is a computed expression",
    ),
    StageTestCase(
        "mixing_sub_proj_exclusion_after_inclusion",
        docs=[{"_id": 1, "a": {"x": 10, "y": 20}}],
        pipeline=[{"$project": {"a": SON([("x", 1), ("y", 0)])}}],
        error_code=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="$project sub-projection should reject exclusion after inclusion",
    ),
    StageTestCase(
        "mixing_sub_proj_inclusion_after_exclusion",
        docs=[{"_id": 1, "a": {"x": 10, "y": 20}}],
        pipeline=[{"$project": {"a": SON([("x", 0), ("y", 1)])}}],
        error_code=PROJECT_INCLUSION_IN_EXCLUSION_ERROR,
        msg="$project sub-projection should reject inclusion after exclusion",
    ),
    StageTestCase(
        "mixing_sub_proj_expression_in_exclusion",
        docs=[{"_id": 1, "a": {"x": 10, "y": 20}}],
        pipeline=[{"$project": {"a": SON([("x", 0), ("y", {"$add": [1, 2]})])}}],
        error_code=PROJECT_OPERATOR_IN_EXCLUSION_ERROR,
        msg="$project sub-projection should reject operator expression in exclusion mode",
    ),
    StageTestCase(
        "mixing_sub_proj_field_path_in_exclusion",
        docs=[{"_id": 1, "a": {"x": 10, "y": 20}}],
        pipeline=[{"$project": {"a": SON([("x", 0), ("y", "$a.x")])}}],
        error_code=PROJECT_VALUE_IN_EXCLUSION_ERROR,
        msg="$project sub-projection should reject field path in exclusion mode",
    ),
]

# Property [Path Collision Errors]: specifying a parent path and a child path
# in the same projection produces an error regardless of order or mode.
PROJECT_PATH_COLLISION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "collision_parent_after_child_inclusion",
        docs=[{"_id": 1, "a": {"b": 1}}],
        pipeline=[{"$project": SON([("a.b", 1), ("a", 1)])}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$project should reject parent path after child path in inclusion mode",
    ),
    StageTestCase(
        "collision_child_after_parent_inclusion",
        docs=[{"_id": 1, "a": {"b": 1}}],
        pipeline=[{"$project": SON([("a", 1), ("a.b", 1)])}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$project should reject child path after parent path in inclusion mode",
    ),
    StageTestCase(
        "collision_parent_after_child_exclusion",
        docs=[{"_id": 1, "a": {"b": 1}}],
        pipeline=[{"$project": SON([("a.b", 0), ("a", 0)])}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$project should reject parent path after child path in exclusion mode",
    ),
    StageTestCase(
        "collision_child_after_parent_exclusion",
        docs=[{"_id": 1, "a": {"b": 1}}],
        pipeline=[{"$project": SON([("a", 0), ("a.b", 0)])}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$project should reject child path after parent path in exclusion mode",
    ),
    StageTestCase(
        "collision_deep_parent_after_child",
        docs=[{"_id": 1, "a": {"b": {"c": 1}}}],
        pipeline=[{"$project": SON([("a.b.c", 1), ("a", 1)])}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$project should reject grandparent path after deeply nested child path",
    ),
    StageTestCase(
        "collision_deep_child_after_parent",
        docs=[{"_id": 1, "a": {"b": {"c": 1}}}],
        pipeline=[{"$project": SON([("a", 1), ("a.b.c", 1)])}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$project should reject deeply nested child path after grandparent path",
    ),
    StageTestCase(
        "collision_mid_level_parent_after_child",
        docs=[{"_id": 1, "a": {"b": {"c": 1}}}],
        pipeline=[{"$project": SON([("a.b.c", 1), ("a.b", 1)])}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$project should reject mid-level parent path after child path",
    ),
    StageTestCase(
        "collision_mid_level_child_after_parent",
        docs=[{"_id": 1, "a": {"b": {"c": 1}}}],
        pipeline=[{"$project": SON([("a.b", 1), ("a.b.c", 1)])}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$project should reject child path after mid-level parent path",
    ),
]

# Property [Argument Validation Errors]: non-document specifications and
# empty document specifications produce errors.
PROJECT_ARGUMENT_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "arg_validation_string",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": "hello"}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a string specification",
    ),
    StageTestCase(
        "arg_validation_int",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": 42}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject an integer specification",
    ),
    StageTestCase(
        "arg_validation_float",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": 3.14}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a float specification",
    ),
    StageTestCase(
        "arg_validation_bool",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": True}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a boolean specification",
    ),
    StageTestCase(
        "arg_validation_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": None}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a null specification",
    ),
    StageTestCase(
        "arg_validation_array",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": [1, 2]}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject an array specification",
    ),
    StageTestCase(
        "arg_validation_int64",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": Int64(42)}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject an Int64 specification",
    ),
    StageTestCase(
        "arg_validation_decimal128",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": Decimal128("3.14")}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a Decimal128 specification",
    ),
    StageTestCase(
        "arg_validation_objectid",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": ObjectId()}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject an ObjectId specification",
    ),
    StageTestCase(
        "arg_validation_datetime",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a datetime specification",
    ),
    StageTestCase(
        "arg_validation_binary",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": Binary(b"\x01")}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a Binary specification",
    ),
    StageTestCase(
        "arg_validation_regex",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": Regex("^abc")}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a Regex specification",
    ),
    StageTestCase(
        "arg_validation_timestamp",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": Timestamp(1, 1)}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a Timestamp specification",
    ),
    StageTestCase(
        "arg_validation_minkey",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": MinKey()}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a MinKey specification",
    ),
    StageTestCase(
        "arg_validation_maxkey",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": MaxKey()}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a MaxKey specification",
    ),
    StageTestCase(
        "arg_validation_code",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": Code("function(){}")}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a Code specification",
    ),
    StageTestCase(
        "arg_validation_codewithscope",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": Code("function(){}", {"x": 1})}],
        error_code=PROJECT_SPEC_NOT_OBJECT_ERROR,
        msg="$project should reject a CodeWithScope specification",
    ),
    StageTestCase(
        "arg_validation_empty_doc",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {}}],
        error_code=PROJECT_EMPTY_SPEC_ERROR,
        msg="$project should reject an empty document specification",
    ),
]

# Property [Field Name Validation Errors]: invalid field names produce errors.
PROJECT_FIELD_NAME_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_name_empty_string",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"": 1}}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$project should reject an empty string field name",
    ),
    StageTestCase(
        "field_name_dollar_prefix",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"$bad": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should reject a $-prefixed field name",
    ),
    StageTestCase(
        "field_name_leading_dot",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {".a": 1}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$project should reject a field path with a leading dot",
    ),
    StageTestCase(
        "field_name_trailing_dot",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a.": 1}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$project should reject a field path with a trailing dot",
    ),
    StageTestCase(
        "field_name_double_dot",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a..b": 1}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$project should reject a field path with a double dot",
    ),
    StageTestCase(
        "field_name_empty_sub_projection",
        docs=[{"_id": 1, "a": {"x": 10}}],
        pipeline=[{"$project": {"a": {}}}],
        error_code=PROJECT_EMPTY_SUB_PROJECTION_ERROR,
        msg="$project should reject an empty sub-projection",
    ),
    StageTestCase(
        "field_name_dollar_natural",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"$natural": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should reject $natural as a field path",
    ),
    StageTestCase(
        "field_name_bare_dollar",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"$": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should reject a bare $ as a field path",
    ),
    StageTestCase(
        "field_name_bare_double_dollar",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"$$": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should reject a bare $$ as a field path",
    ),
    StageTestCase(
        "field_name_nested_leading_dollar",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a.$b": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should reject a leading $ in a nested path component",
    ),
    StageTestCase(
        "field_name_depth_exceeds_200",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {".".join(["a"] * 201): 1}}],
        error_code=OVERFLOW_ERROR,
        msg="$project should reject a field path exceeding 200 components",
    ),
]

# Property [Expression Validation Errors]: unrecognized or misused expression
# operators in a sub-document produce errors.
PROJECT_EXPRESSION_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "expr_unrecognized_operator",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": {"$bogus": 1}}}],
        error_code=PROJECT_UNKNOWN_EXPRESSION_ERROR,
        msg="$project should reject an unrecognized $-prefixed operator",
    ),
    StageTestCase(
        "expr_multiple_dollar_keys",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": SON([("$add", [1, 2]), ("$subtract", [3, 1])])}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should reject multiple $-prefixed keys in a sub-document",
    ),
    StageTestCase(
        "expr_mixed_dollar_and_non_dollar_keys",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"a": SON([("$add", [1, 2]), ("x", 1)])}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should reject mixed $ and non-$ keys in a sub-document",
    ),
    StageTestCase(
        "expr_elemmatch_in_aggregation",
        docs=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}],
        pipeline=[{"$project": {"a": {"$elemMatch": {"x": 1}}}}],
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$project should reject $elemMatch in aggregation context",
    ),
    StageTestCase(
        "expr_slice_find_syntax",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$project": {"a": {"$slice": 2}}}],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$project should reject $slice with find-projection syntax",
    ),
]

# Property [Error Precedence]: when multiple errors exist, field name
# validation errors take priority over mixing restriction errors.
PROJECT_ERROR_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_first_field_determines_error_dollar_first",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": SON([("$bad", 1), (".a", 1)])}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$project should report the error from the first invalid field in document order",
    ),
    StageTestCase(
        "precedence_first_field_determines_error_dot_first",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": SON([(".a", 1), ("$bad", 1)])}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg=(
            "$project should report the leading-dot error when it appears"
            " before the $-prefix error in document order"
        ),
    ),
    StageTestCase(
        "precedence_empty_before_dollar",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": SON([("", 1), ("$bad", 1)])}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg=(
            "$project should report empty string error when it appears"
            " before a $-prefix error in document order"
        ),
    ),
    StageTestCase(
        "precedence_dollar_before_empty",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": SON([("$bad", 1), ("", 1)])}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg=(
            "$project should report $-prefix error when it appears"
            " before an empty string error in document order"
        ),
    ),
    StageTestCase(
        "precedence_field_name_over_mixing",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$project": SON([("a", 1), ("", 0)])}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg=(
            "$project should report field name validation error even"
            " when the same field would also cause a mixing restriction error"
        ),
    ),
]

PROJECT_ERROR_TESTS = (
    PROJECT_MIXING_RESTRICTION_ERROR_TESTS
    + PROJECT_PATH_COLLISION_ERROR_TESTS
    + PROJECT_ARGUMENT_VALIDATION_ERROR_TESTS
    + PROJECT_FIELD_NAME_VALIDATION_ERROR_TESTS
    + PROJECT_EXPRESSION_VALIDATION_ERROR_TESTS
    + PROJECT_ERROR_PRECEDENCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PROJECT_ERROR_TESTS))
def test_project_errors(collection: Any, test_case: StageTestCase) -> None:
    """Test $project error cases."""
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
