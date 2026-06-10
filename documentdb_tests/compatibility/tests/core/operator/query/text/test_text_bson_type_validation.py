"""Tests for $text query operator BSON type validation.

Verifies that $text parameter values reject invalid BSON types and accept valid types.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

TEXT_PARAM_BSON_TYPE_SPECS = [
    BsonTypeTestCase(
        id="search",
        msg="$text $search should reject non-string types",
        keyword="$search",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="language",
        msg="$text $language should reject non-string types",
        keyword="$language",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.STRING: "english"},
    ),
    BsonTypeTestCase(
        id="caseSensitive",
        msg="$text $caseSensitive should reject non-boolean types",
        keyword="$caseSensitive",
        valid_types=[BsonType.BOOL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="diacriticSensitive",
        msg="$text $diacriticSensitive should reject non-boolean types",
        keyword="$diacriticSensitive",
        valid_types=[BsonType.BOOL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]


def _build_text_filter(spec, sample_value):
    """Build a $text filter with the given keyword set to sample_value."""
    text_expr = {"$search": "hello"}
    text_expr[spec.keyword] = sample_value
    return {"$text": text_expr}


REJECTION_CASES = generate_bson_rejection_test_cases(TEXT_PARAM_BSON_TYPE_SPECS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_text_param_type_rejected(collection, bson_type, sample_value, spec):
    """Test $text rejects invalid BSON types for its parameters."""
    collection.create_index([("content", "text")])
    query = _build_text_filter(spec, sample_value)
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TEXT_PARAM_BSON_TYPE_SPECS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_text_param_type_accepted(collection, bson_type, sample_value, spec):
    """Test $text accepts valid BSON types for its parameters."""
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "hello world"}])
    query = _build_text_filter(spec, sample_value)
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertSuccess(
        result,
        [{"_id": 1, "content": "hello world"}],
        ignore_doc_order=True,
        msg=f"{spec.keyword} should accept {bson_type.value}",
    )
