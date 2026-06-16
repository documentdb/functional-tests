"""Tests for the $replaceWith aggregation stage."""

from __future__ import annotations

from datetime import datetime, timezone

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

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    LET_UNDEFINED_VARIABLE_ERROR,
    REPLACE_ROOT_NON_OBJECT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness]: any argument resolving to a non-object, non-null
# BSON type produces an error with no coercion to a document.
REPLACEWITH_TYPE_STRICTNESS_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"type_{tid}",
        docs=[{"_id": 1, "v": val}],
        pipeline=[{"$replaceWith": "$v"}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg=f"$replaceWith should reject a {tid} argument with no coercion",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 7),
        ("int64", Int64(9_999_999_999)),
        ("double", 3.5),
        ("decimal128", Decimal128("123.456")),
        ("bool_true", True),
        ("bool_false", False),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1_700_000_000, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("^abc", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Arrival-Path Independence]: a non-object argument is rejected
# regardless of how the value arrives, with no coercion route.
REPLACEWITH_ARRIVAL_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "arrival_literal_scalar",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"$literal": "hello"}}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a $literal-wrapped scalar with no coercion",
    ),
    StageTestCase(
        "arrival_bare_scalar",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": ""}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a bare empty string treated as a literal scalar",
    ),
    StageTestCase(
        "arrival_expression_object_to_array",
        docs=[{"_id": 1, "a": {"k": 1}}],
        pipeline=[{"$replaceWith": {"$objectToArray": "$a"}}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject an expression resolving to an array with no coercion",
    ),
    StageTestCase(
        "arrival_system_variable_non_object",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": "$$NOW"}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a system variable resolving to a non-object",
    ),
]

# Property [Array Rejection]: an array argument in any form produces an error and
# is never unwrapped into an argument list.
REPLACEWITH_ARRAY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "array_literal_of_objects",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": [{"a": 1}]}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a literal array without unwrapping it",
    ),
    StageTestCase(
        "array_empty_literal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": []}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject an empty array literal",
    ),
    StageTestCase(
        "array_multi_element_literal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": [{"a": 1}, {"b": 2}]}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a multi-element array literal",
    ),
    StageTestCase(
        "array_stored_reference",
        docs=[{"_id": 1, "items": [{"a": 1}, {"b": 2}]}],
        pipeline=[{"$replaceWith": "$items"}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a stored array field reference",
    ),
]

# Property [Null and Missing Behavior]: an argument resolving to null or missing
# produces the non-object error, with no coercion or pass-through.
REPLACEWITH_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_literal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"$literal": None}}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a literal null argument with no coercion",
    ),
    StageTestCase(
        "null_stored_field",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$replaceWith": "$a"}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a stored null field value with no coercion",
    ),
    StageTestCase(
        "null_ifnull",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": {"$ifNull": ["$nonexistent", None]}}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject an $ifNull resolving to null",
    ),
    StageTestCase(
        "missing_field_reference",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": "$nonexistent"}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a reference to a non-existent field",
    ),
    StageTestCase(
        "missing_deep_path",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": "$nonexistent.b.c"}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject a deep path through a missing field",
    ),
    StageTestCase(
        "missing_remove_variable",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": "$$REMOVE"}],
        error_code=REPLACE_ROOT_NON_OBJECT_ERROR,
        msg="$replaceWith should reject $$REMOVE used as the whole argument",
    ),
]

# Property [Undefined Variable Rejection]: an argument referencing a variable
# that is not defined in scope is rejected with an undefined-variable error
# rather than the non-object error, taking a distinct code path from a value
# that resolves to a non-object.
REPLACEWITH_UNDEFINED_VARIABLE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "undefined_redact_variable",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": "$$DESCEND"}],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$replaceWith should reject a redact-only variable undefined in this scope",
    ),
    StageTestCase(
        "undefined_user_variable",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$replaceWith": "$$undefinedVar"}],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$replaceWith should reject a user variable that is not defined in scope",
    ),
]

REPLACEWITH_NON_OBJECT_ERROR_TESTS: list[StageTestCase] = (
    REPLACEWITH_TYPE_STRICTNESS_TESTS
    + REPLACEWITH_ARRIVAL_PATH_TESTS
    + REPLACEWITH_ARRAY_TESTS
    + REPLACEWITH_NULL_MISSING_TESTS
    + REPLACEWITH_UNDEFINED_VARIABLE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEWITH_NON_OBJECT_ERROR_TESTS))
def test_replaceWith_non_object_error_cases(collection, test_case: StageTestCase):
    """Test $replaceWith non object error cases."""
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
