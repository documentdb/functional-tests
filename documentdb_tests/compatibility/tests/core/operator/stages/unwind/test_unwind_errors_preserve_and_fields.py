"""Tests for $unwind stage — preserveNullAndEmptyArrays type validation and unrecognized fields."""

from __future__ import annotations

from datetime import datetime

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
    UNWIND_PRESERVE_NULL_TYPE_ERROR,
    UNWIND_UNRECOGNIZED_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

# Property [preserveNullAndEmptyArrays Type Validation]: all non-boolean BSON
# types for preserveNullAndEmptyArrays are rejected with a type error; no
# truthy/falsy coercion is performed, and expression objects and field
# references are rejected as their literal types.
UNWIND_PRESERVE_NULL_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "preserve_type_int32_zero",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": 0}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject int32 0 (no falsy coercion)",
    ),
    StageTestCase(
        "preserve_type_int32_one",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": 1}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject int32 1 (no truthy coercion)",
    ),
    StageTestCase(
        "preserve_type_int64",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Int64(1)}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Int64",
    ),
    StageTestCase(
        "preserve_type_double_zero",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": DOUBLE_ZERO}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject double 0.0 (no falsy coercion)",
    ),
    StageTestCase(
        "preserve_type_double_one",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": 1.0}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject double 1.0 (no truthy coercion)",
    ),
    StageTestCase(
        "preserve_type_decimal128",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Decimal128("1")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Decimal128",
    ),
    StageTestCase(
        "preserve_type_string",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": "true"}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject string",
    ),
    StageTestCase(
        "preserve_type_null",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": None}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject null (not treated as default false)",
    ),
    StageTestCase(
        "preserve_type_array",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": []}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject array",
    ),
    StageTestCase(
        "preserve_type_object",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": {"x": 1}}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject object",
    ),
    StageTestCase(
        "preserve_type_objectid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "preserveNullAndEmptyArrays": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject ObjectId",
    ),
    StageTestCase(
        "preserve_type_datetime",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": datetime(2024, 1, 1)}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject datetime",
    ),
    StageTestCase(
        "preserve_type_timestamp",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Timestamp(1, 1)}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Timestamp",
    ),
    StageTestCase(
        "preserve_type_binary",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Binary(b"\x01")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Binary",
    ),
    StageTestCase(
        "preserve_type_regex",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Regex("^a")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Regex",
    ),
    StageTestCase(
        "preserve_type_code",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Code("x")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Code",
    ),
    StageTestCase(
        "preserve_type_code_with_scope",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Code("x", {})}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Code with scope",
    ),
    StageTestCase(
        "preserve_type_minkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": MinKey()}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject MinKey",
    ),
    StageTestCase(
        "preserve_type_maxkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": MaxKey()}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject MaxKey",
    ),
    StageTestCase(
        "preserve_type_expression_literal",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": {"$literal": True}}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject expression object {$literal: true}",
    ),
    StageTestCase(
        "preserve_type_field_reference",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": "$flag"}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject field reference string",
    ),
]

# Property [Unrecognized Fields]: unrecognized fields in the document form
# produce an unrecognized field error, and this error takes precedence over
# a missing path error.
UNWIND_UNRECOGNIZED_FIELD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unrecognized_field_with_valid_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "badField": True}}],
        error_code=UNWIND_UNRECOGNIZED_FIELD_ERROR,
        msg="$unwind should reject unrecognized field in document form",
    ),
    StageTestCase(
        "unrecognized_field_precedes_missing_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"badField": True}}],
        error_code=UNWIND_UNRECOGNIZED_FIELD_ERROR,
        msg="$unwind unrecognized field error should take precedence over missing path error",
    ),
]

UNWIND_PRESERVE_AND_FIELDS_ALL_TESTS = (
    UNWIND_PRESERVE_NULL_TYPE_TESTS + UNWIND_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_PRESERVE_AND_FIELDS_ALL_TESTS))
def test_unwind_preserve_and_field_errors(collection, test_case: StageTestCase):
    """Test $unwind preserveNullAndEmptyArrays type validation and unrecognized field errors."""
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
