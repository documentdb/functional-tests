"""Tests for $sample stage spec shape errors."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SAMPLE_SIZE_MISSING_ERROR,
    SAMPLE_SIZE_NOT_NUMERIC_ERROR,
    SAMPLE_SIZE_NOT_POSITIVE_ERROR,
    SAMPLE_SPEC_NOT_OBJECT_ERROR,
    SAMPLE_UNRECOGNIZED_OPTION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Spec Must Be Object]: the $sample stage argument must be a
# document; any non-document type produces a spec-not-object error.
SAMPLE_SPEC_NOT_OBJECT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_bare_int",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": 5}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare int as stage argument",
    ),
    StageTestCase(
        "spec_bare_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Int64(5)}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare int64 as stage argument",
    ),
    StageTestCase(
        "spec_bare_double",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": 3.14}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare double as stage argument",
    ),
    StageTestCase(
        "spec_bare_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Decimal128("5")}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare Decimal128 as stage argument",
    ),
    StageTestCase(
        "spec_bare_string",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": "hello"}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare string as stage argument",
    ),
    StageTestCase(
        "spec_bare_null",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": None}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare null as stage argument",
    ),
    StageTestCase(
        "spec_bare_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": True}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare bool as stage argument",
    ),
    StageTestCase(
        "spec_bare_array",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": [1, 2]}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare array as stage argument",
    ),
    StageTestCase(
        "spec_bare_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": ObjectId("507f1f77bcf86cd799439011")}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare ObjectId as stage argument",
    ),
    StageTestCase(
        "spec_bare_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": datetime(2023, 1, 1)}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare datetime as stage argument",
    ),
    StageTestCase(
        "spec_bare_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Timestamp(0, 1)}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare Timestamp as stage argument",
    ),
    StageTestCase(
        "spec_bare_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Binary(b"\x01")}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare Binary as stage argument",
    ),
    StageTestCase(
        "spec_bare_binary_uuid",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Binary.from_uuid(UUID("12345678-1234-5678-1234-567812345678"))}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare Binary UUID as stage argument",
    ),
    StageTestCase(
        "spec_bare_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Regex("abc")}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare Regex as stage argument",
    ),
    StageTestCase(
        "spec_bare_code",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Code("function(){}")}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare Code as stage argument",
    ),
    StageTestCase(
        "spec_bare_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": Code("function(){return x}", {"x": 1})}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare Code with scope as stage argument",
    ),
    StageTestCase(
        "spec_bare_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": MinKey()}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare MinKey as stage argument",
    ),
    StageTestCase(
        "spec_bare_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": MaxKey()}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should reject a bare MaxKey as stage argument",
    ),
]

# Property [Unrecognized Option]: extra or misspelled keys in the $sample
# document produce an unrecognized-option error.
SAMPLE_UNRECOGNIZED_OPTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "extra_key_with_size",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": 3, "extra": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should reject extra keys alongside size",
    ),
    StageTestCase(
        "extra_key_without_size",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"extra": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should reject extra keys without size",
    ),
    StageTestCase(
        "case_sensitive_Size",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"Size": 3}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample key matching is case-sensitive: Size",
    ),
    StageTestCase(
        "whitespace_leading_space",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {" size": 3}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample key matching is whitespace-sensitive: leading space",
    ),
    StageTestCase(
        "whitespace_trailing_space",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size ": 3}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample key matching is whitespace-sensitive: trailing space",
    ),
    StageTestCase(
        "multiple_extra_keys",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": 3, "alpha": 1, "beta": 2}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should reject multiple extra keys",
    ),
    StageTestCase(
        "unicode_key",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": 3, "\u00fc\u00f1\u00ef\u00e7\u00f6d\u00e9": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should reject unicode extra key",
    ),
    StageTestCase(
        "dollar_prefixed_key",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": 3, "$size": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should reject dollar-prefixed extra key",
    ),
    StageTestCase(
        "dotted_key",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": 3, "size.n": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should reject dotted extra key",
    ),
]

# Property [Validation Precedence]: validation errors follow a fixed
# precedence where earlier checks mask later ones.
SAMPLE_VALIDATION_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_type_over_extra_key",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": "bad", "extra": 1}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample type error should take precedence over extra-key error",
    ),
    StageTestCase(
        "precedence_extra_key_over_not_positive",
        docs=[{"_id": 1}],
        pipeline=[{"$sample": {"size": -1, "extra": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample extra-key error should take precedence over not-positive error",
    ),
]

# Property [Errors on Non-Existent Collection]: every validation error fires
# even when the collection does not exist, confirming that the server rejects
# invalid $sample parameters without requiring any input documents.
SAMPLE_NONEXISTENT_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nonexistent_collection_type_error",
        docs=None,
        pipeline=[{"$sample": {"size": "bad"}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should produce type error even on non-existent collection",
    ),
    StageTestCase(
        "nonexistent_collection_not_positive",
        docs=None,
        pipeline=[{"$sample": {"size": -1}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should produce not-positive error even on non-existent collection",
    ),
    StageTestCase(
        "nonexistent_collection_missing_size",
        docs=None,
        pipeline=[{"$sample": {}}],
        error_code=SAMPLE_SIZE_MISSING_ERROR,
        msg="$sample should produce missing-size error even on non-existent collection",
    ),
    StageTestCase(
        "nonexistent_collection_spec_not_object",
        docs=None,
        pipeline=[{"$sample": 1}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should produce spec-not-object error even on non-existent collection",
    ),
    StageTestCase(
        "nonexistent_collection_unrecognized_option",
        docs=None,
        pipeline=[{"$sample": {"extra": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should produce unrecognized-option error even on non-existent collection",
    ),
]

# Property [Errors on Empty Collection]: every validation error fires even
# when the collection exists but is empty.
SAMPLE_EMPTY_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection_type_error",
        docs=[],
        pipeline=[{"$sample": {"size": "bad"}}],
        error_code=SAMPLE_SIZE_NOT_NUMERIC_ERROR,
        msg="$sample should produce type error even on empty collection",
    ),
    StageTestCase(
        "empty_collection_not_positive",
        docs=[],
        pipeline=[{"$sample": {"size": -1}}],
        error_code=SAMPLE_SIZE_NOT_POSITIVE_ERROR,
        msg="$sample should produce not-positive error even on empty collection",
    ),
    StageTestCase(
        "empty_collection_missing_size",
        docs=[],
        pipeline=[{"$sample": {}}],
        error_code=SAMPLE_SIZE_MISSING_ERROR,
        msg="$sample should produce missing-size error even on empty collection",
    ),
    StageTestCase(
        "empty_collection_spec_not_object",
        docs=[],
        pipeline=[{"$sample": 1}],
        error_code=SAMPLE_SPEC_NOT_OBJECT_ERROR,
        msg="$sample should produce spec-not-object error even on empty collection",
    ),
    StageTestCase(
        "empty_collection_unrecognized_option",
        docs=[],
        pipeline=[{"$sample": {"extra": 1}}],
        error_code=SAMPLE_UNRECOGNIZED_OPTION_ERROR,
        msg="$sample should produce unrecognized-option error even on empty collection",
    ),
]

SAMPLE_SPEC_ERROR_TESTS = (
    SAMPLE_SPEC_NOT_OBJECT_ERROR_TESTS
    + SAMPLE_UNRECOGNIZED_OPTION_ERROR_TESTS
    + SAMPLE_VALIDATION_PRECEDENCE_TESTS
    + SAMPLE_NONEXISTENT_COLLECTION_ERROR_TESTS
    + SAMPLE_EMPTY_COLLECTION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SAMPLE_SPEC_ERROR_TESTS))
def test_sample_spec_errors(collection, test_case: StageTestCase):
    """Test $sample stage spec shape errors."""
    if test_case.setup:
        test_case.setup(collection)
    if test_case.docs:
        collection.insert_many(test_case.docs)
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
