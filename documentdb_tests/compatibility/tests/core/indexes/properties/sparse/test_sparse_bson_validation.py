"""
Tests for sparse index option BSON type validation.

Verifies that the sparse field in createIndexes rejects invalid BSON types
with expected error codes and accepts valid BSON types (bool and numerics).
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

SPARSE_OPTION_PARAMS = [
    BsonTypeTestCase(
        id="sparse",
        msg="sparse should reject non-bool/non-numeric types",
        keyword="sparse",
        valid_types=[BsonType.BOOL, BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(SPARSE_OPTION_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SPARSE_OPTION_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_sparse_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test createIndexes rejects invalid BSON types for sparse option."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_sparse", "sparse": sample_value}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_sparse_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test createIndexes accepts valid BSON types for sparse option."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_sparse", "sparse": sample_value}],
        },
    )
    assertNotError(result, msg=f"sparse should accept {bson_type.value}")
