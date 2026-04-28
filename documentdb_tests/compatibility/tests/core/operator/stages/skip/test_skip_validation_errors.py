"""Tests for $skip stage validation errors: wrong types, syntax, and precedence."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
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
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    SKIP_INVALID_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty and Non-Existent Collection Errors]: Invalid skip values
# produce the same validation errors on empty and non-existent collections as
# on populated ones.
SKIP_EMPTY_NONEXISTENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "invalid_skip_empty_collection",
        docs=[],
        pipeline=[{"$skip": "bad"}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject invalid value on empty collection",
    ),
    StageTestCase(
        "invalid_skip_nonexistent_collection",
        docs=None,
        pipeline=[{"$skip": "bad"}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject invalid value on non-existent collection",
    ),
    StageTestCase(
        "extra_field_empty_collection",
        docs=[],
        pipeline=[{"$skip": 1, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$skip extra field error should fire on empty collection",
    ),
    StageTestCase(
        "extra_field_nonexistent_collection",
        docs=None,
        pipeline=[{"$skip": 1, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$skip extra field error should fire on non-existent collection",
    ),
]

# Property [Non-Numeric Type Rejection]: $skip rejects all non-numeric BSON
# types, arrays, objects, expression-like objects, and dollar-prefixed strings
# with an error.
SKIP_NON_NUMERIC_TYPE_REJECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": None}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject null",
    ),
    StageTestCase(
        "string_value",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": "abc"}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject string values",
    ),
    StageTestCase(
        "bool_true",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": True}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject bool true",
    ),
    StageTestCase(
        "bool_false",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": False}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject bool false",
    ),
    StageTestCase(
        "objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject ObjectId values",
    ),
    StageTestCase(
        "datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject datetime values",
    ),
    StageTestCase(
        "timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Timestamp(100, 1)}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Timestamp values",
    ),
    StageTestCase(
        "binary",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Binary(b"\x01\x02")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Binary values",
    ),
    StageTestCase(
        "regex",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Regex("abc", "i")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Regex values",
    ),
    StageTestCase(
        "code",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Code("function(){}")}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Code values",
    ),
    StageTestCase(
        "code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": Code("function(){}", {})}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject Code with scope values",
    ),
    StageTestCase(
        "minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": MinKey()}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject MinKey",
    ),
    StageTestCase(
        "maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": MaxKey()}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject MaxKey",
    ),
    StageTestCase(
        "empty_array",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": []}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject empty array",
    ),
    StageTestCase(
        "single_element_array",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": [1]}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject single-element array",
    ),
    StageTestCase(
        "multi_element_array",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": [1, 2, 3]}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject multi-element array",
    ),
    StageTestCase(
        "nested_array",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": [[1]]}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject nested array",
    ),
    StageTestCase(
        "array_with_null",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": [None]}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject array with null element",
    ),
    StageTestCase(
        "empty_object",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": {}}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject empty object",
    ),
    StageTestCase(
        "object_with_fields",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": {"a": 1}}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject object with fields",
    ),
    StageTestCase(
        "expression_like_object",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": {"$add": [1, 2]}}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject expression-like objects without evaluating them",
    ),
    StageTestCase(
        "literal_object",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": {"$literal": 3}}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject $literal - not recognized in stage context",
    ),
    StageTestCase(
        "dollar_prefixed_field_path",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": "$x"}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject dollar-prefixed strings as field paths",
    ),
    StageTestCase(
        "dollar_prefixed_system_var",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": "$$ROOT"}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="$skip should reject system variable references",
    ),
]

# Property [Syntax Validation]: A pipeline stage document must contain exactly
# one field; extra keys alongside $skip produce an error.
SKIP_SYNTAX_VALIDATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "extra_key_operator",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": 1, "$limit": 2}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$skip stage with extra operator key should produce error",
    ),
    StageTestCase(
        "extra_key_non_operator",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": 1, "foo": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$skip stage with extra non-operator key should produce error",
    ),
]

# Property [Cross-Stage Error Precedence]: when multiple stages have invalid
# values, the first invalid stage by position produces the error.
SKIP_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "first_string_then_negative",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": "bad"}, {"$skip": -1}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="First invalid stage (string) should produce its error code",
    ),
    StageTestCase(
        "first_negative_then_string",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": -1}, {"$skip": "bad"}],
        error_code=SKIP_INVALID_ARGUMENT_ERROR,
        msg="First invalid stage (negative) should produce its error code",
    ),
]

SKIP_VALIDATION_ERROR_TESTS: list[StageTestCase] = (
    SKIP_EMPTY_NONEXISTENT_ERROR_TESTS
    + SKIP_NON_NUMERIC_TYPE_REJECTION_TESTS
    + SKIP_SYNTAX_VALIDATION_TESTS
    + SKIP_PRECEDENCE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SKIP_VALIDATION_ERROR_TESTS))
def test_skip_validation_errors(collection, test_case: StageTestCase):
    """Test $skip stage validation errors for wrong types and syntax."""
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
