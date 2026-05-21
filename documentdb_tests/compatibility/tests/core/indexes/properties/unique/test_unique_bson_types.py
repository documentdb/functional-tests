"""Tests for unique index option BSON type validation.

Verifies that createIndexes rejects invalid BSON types for the unique
option and accepts valid numeric/boolean types (truthy values are
treated as unique:true, falsy as unique:false).
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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

UNIQUE_BSON_PARAMS = [
    BsonTypeTestCase(
        id="unique",
        msg="unique should reject non-numeric, non-boolean types",
        keyword="unique",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL, BsonType.BOOL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={
            BsonType.DOUBLE: 1.0,
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DECIMAL: Decimal128("1"),
            BsonType.BOOL: True,
        },
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(UNIQUE_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_unique_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test unique rejects invalid BSON types."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"a": 1},
                    "name": "idx_unique_bson",
                    "unique": sample_value,
                }
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(UNIQUE_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_unique_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test unique accepts valid numeric/boolean BSON types."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"a": 1},
                    "name": "idx_unique_bson",
                    "unique": sample_value,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg=f"unique should accept {bson_type.value}",
    )
