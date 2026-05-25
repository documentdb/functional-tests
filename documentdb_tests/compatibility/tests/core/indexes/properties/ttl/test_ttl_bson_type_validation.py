"""Tests for TTL index expireAfterSeconds BSON type validation.

Verifies that createIndexes rejects invalid BSON types for expireAfterSeconds
and accepts valid numeric BSON types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import CANNOT_CREATE_INDEX_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

TTL_BSON_PARAMS = [
    BsonTypeTestCase(
        id="expireAfterSeconds",
        msg="expireAfterSeconds should reject non-numeric types",
        keyword="expireAfterSeconds",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=CANNOT_CREATE_INDEX_ERROR,
        valid_inputs={
            BsonType.DOUBLE: 3600.0,
            BsonType.INT: 3600,
            BsonType.LONG: Int64(3600),
            BsonType.DECIMAL: Decimal128("3600"),
        },
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(TTL_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_ttl_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test expireAfterSeconds rejects invalid BSON types."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"dateField": 1},
                    "name": "ttl_bson_test",
                    "expireAfterSeconds": sample_value,
                }
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TTL_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_ttl_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test expireAfterSeconds accepts valid numeric BSON types."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"dateField": 1},
                    "name": "ttl_bson_test",
                    "expireAfterSeconds": sample_value,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg=f"expireAfterSeconds should accept {bson_type.value}",
    )
