"""Tests for text index BSON type validation.

Verifies that text index key specifier and options reject invalid BSON types
and accept valid types.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import CANNOT_CREATE_INDEX_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.text_search

# Default text index spec — tests override individual keywords with sample values
_DEFAULT_INDEX = {"key": {"content": "text"}, "name": "test_idx"}

TEXT_INDEX_PARAMS = [
    BsonTypeTestCase(
        id="key_specifier",
        msg="text index key specifier should only accept the string 'text'",
        keyword="key_specifier",
        valid_types=[BsonType.STRING],
        # Numeric types don't error but create a regular index instead of a text index,
        # so they are neither valid text key specifiers nor rejected — skip them.
        skip_rejection_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=CANNOT_CREATE_INDEX_ERROR,
        valid_inputs={
            BsonType.STRING: "text",
        },
    ),
    BsonTypeTestCase(
        id="default_language",
        msg="default_language should only accept string",
        keyword="default_language",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={
            BsonType.STRING: "english",
        },
    ),
    BsonTypeTestCase(
        id="language_override",
        msg="language_override should only accept string",
        keyword="language_override",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={
            BsonType.STRING: "language",
        },
    ),
    BsonTypeTestCase(
        id="weights",
        msg="weights should only accept object",
        keyword="weights",
        valid_types=[BsonType.OBJECT],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={
            BsonType.STRING: CANNOT_CREATE_INDEX_ERROR,
            BsonType.ARRAY: CANNOT_CREATE_INDEX_ERROR,
        },
        valid_inputs={
            BsonType.OBJECT: {"content": 5},
        },
    ),
    BsonTypeTestCase(
        id="textIndexVersion",
        msg="textIndexVersion should only accept numeric",
        keyword="textIndexVersion",
        valid_types=[BsonType.INT, BsonType.LONG, BsonType.DOUBLE],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={
            BsonType.DECIMAL: CANNOT_CREATE_INDEX_ERROR,
        },
        valid_inputs={
            BsonType.INT: 3,
            BsonType.LONG: 3,
            BsonType.DOUBLE: 3.0,
        },
    ),
]


def _build_index(spec, sample_value):
    """Build index spec by overriding the keyword in the default index."""
    if spec.keyword == "key_specifier":
        return {**_DEFAULT_INDEX, "key": {"content": sample_value}}
    return {**_DEFAULT_INDEX, spec.keyword: sample_value}


REJECTION_CASES = generate_bson_rejection_test_cases(TEXT_INDEX_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_text_index_type_rejected(collection, bson_type, sample_value, spec):
    """Test text index creation rejects invalid BSON types."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [_build_index(spec, sample_value)]},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TEXT_INDEX_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_text_index_type_accepted(collection, bson_type, sample_value, spec):
    """Test text index creation accepts valid BSON types."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [_build_index(spec, sample_value)]},
    )
    assertNotError(result, msg=f"{spec.keyword} should accept {bson_type.value}")
