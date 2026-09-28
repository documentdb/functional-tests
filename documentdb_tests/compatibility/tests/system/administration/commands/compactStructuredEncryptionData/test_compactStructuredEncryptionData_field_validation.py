"""Tests for compactStructuredEncryptionData command field validation.

Covers collection name type validation (§19 representative case),
compactionTokens BSON type rejection, and missing field errors.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    NOT_ENCRYPTED_COLLECTION_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

# Property [CompactionTokens Type Rejection]: compactStructuredEncryptionData rejects
# non-document types for the compactionTokens field.
BSON_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="compactionTokens_type",
        msg="compactionTokens should reject non-document types",
        keyword="compactionTokens",
        valid_types=[BsonType.OBJECT],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(BSON_TYPE_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(BSON_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_compactStructuredEncryptionData_rejects_invalid_compactionTokens_type(
    collection, bson_type, sample_value, spec
):
    """Test compactStructuredEncryptionData rejects invalid BSON types for compactionTokens."""
    cmd = {
        "compactStructuredEncryptionData": collection.name,
        "compactionTokens": sample_value,
    }
    result = execute_command(collection, cmd)
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_compactStructuredEncryptionData_accepts_valid_compactionTokens_type(
    collection, bson_type, sample_value, spec
):
    """Test compactStructuredEncryptionData accepts document type for compactionTokens.

    The command accepts the type but fails because the collection is not encrypted.
    Error 6346807 confirms the type was accepted and processing continued.
    """
    collection.insert_one({"_id": 1})
    cmd = {
        "compactStructuredEncryptionData": collection.name,
        "compactionTokens": sample_value,
    }
    result = execute_command(collection, cmd)
    assertFailureCode(
        result,
        NOT_ENCRYPTED_COLLECTION_ERROR,
        msg=spec.msg,
    )


def test_compactStructuredEncryptionData_rejects_non_string_collection_name(collection):
    """Test compactStructuredEncryptionData rejects non-string collection name."""
    cmd = {"compactStructuredEncryptionData": 1, "compactionTokens": {}}
    result = execute_command(collection, cmd)
    assertFailureCode(
        result,
        INVALID_NAMESPACE_ERROR,
        msg="compactStructuredEncryptionData should reject non-string collection name",
    )


def test_compactStructuredEncryptionData_rejects_empty_collection_name(collection):
    """Test compactStructuredEncryptionData rejects empty string collection name."""
    cmd = {"compactStructuredEncryptionData": "", "compactionTokens": {}}
    result = execute_command(collection, cmd)
    assertFailureCode(
        result,
        INVALID_NAMESPACE_ERROR,
        msg="compactStructuredEncryptionData should reject empty collection name",
    )


def test_compactStructuredEncryptionData_missing_compactionTokens(collection):
    """Test compactStructuredEncryptionData requires compactionTokens field."""
    collection.insert_one({"_id": 1})
    cmd = {"compactStructuredEncryptionData": collection.name}
    result = execute_command(collection, cmd)
    assertFailureCode(
        result,
        MISSING_FIELD_ERROR,
        msg="compactStructuredEncryptionData should error when compactionTokens is missing",
    )
