"""Tests for wildcard index BSON type validation."""

import pytest
from bson import Int64
from bson.decimal128 import Decimal128

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index


WILDCARD_BSON_PARAMS = [
    BsonTypeTestCase(
        id="wildcardProjection",
        msg="wildcardProjection should reject non-document types",
        keyword="wildcardProjection",
        valid_types=[BsonType.OBJECT],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.OBJECT: {"a": 1}},
    ),
    BsonTypeTestCase(
        id="wildcard_key_value",
        msg="wildcard index key value should reject non-numeric types",
        keyword="key_value",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=CANNOT_CREATE_INDEX_ERROR,
        # STRING is skipped here because some strings name valid special index
        # types (e.g. "2d", "2dsphere", "hashed", "wildcard"); string key values
        # are covered explicitly in test_wildcard_errors.py.
        skip_rejection_types=[BsonType.STRING],
        valid_inputs={
            BsonType.DOUBLE: 1.0,
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DECIMAL: Decimal128("1"),
        },
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(WILDCARD_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(WILDCARD_BSON_PARAMS)


def _build_command(collection, spec, sample_value):
    """Build the appropriate createIndexes command for the given spec and sample value."""
    if spec.id == "wildcardProjection":
        return execute_command(
            collection,
            {
                "createIndexes": collection.name,
                "indexes": [
                    {
                        "key": {"$**": 1},
                        "name": "wc_bson_test",
                        "wildcardProjection": sample_value,
                    }
                ],
            },
        )
    else:
        return execute_command(
            collection,
            {
                "createIndexes": collection.name,
                "indexes": [{"key": {"$**": sample_value}, "name": "wc_bson_test"}],
            },
        )


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_wildcard_rejects_invalid_bson_type(collection, bson_type, sample_value, spec):
    """Test wildcard index options reject invalid BSON types."""
    result = _build_command(collection, spec, sample_value)
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_wildcard_accepts_valid_bson_type(collection, bson_type, sample_value, spec):
    """Test wildcard index options accept valid BSON types."""
    result = _build_command(collection, spec, sample_value)
    assertNotError(result, msg=f"{spec.id} should accept {bson_type.value}")
