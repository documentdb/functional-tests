"""
Tests for positional ($) projection BSON type validation.

Verifies that $ projection correctly validates the projection value.
Only 1 (inclusion) is valid for positional projection. All other BSON types
as the projection value should error.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    PROJECT_INVALID_LITERAL_VALUE_ERROR,
    PROJECTION_INVALID_OBJECT_VALUE_ERROR,
)
from documentdb_tests.framework.executor import execute_command

POSITIONAL_PARAMS = [
    BsonTypeTestCase(
        id="positional_projection_value",
        msg="$ projection value type validation",
        keyword="$",
        valid_types=[
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.BOOL,
        ],
        valid_inputs={
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DOUBLE: 1.0,
            BsonType.DECIMAL: Decimal128("1"),
            BsonType.BOOL: True,
        },
        default_error_code=PROJECT_INVALID_LITERAL_VALUE_ERROR,
        error_code_overrides={
            BsonType.OBJECT: PROJECTION_INVALID_OBJECT_VALUE_ERROR,
        },
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(POSITIONAL_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_positional_projection_value_accepted(collection, bson_type, sample_value, spec):
    """Test $ projection accepts valid projection values."""
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$gte": 20}},
            "projection": {"arr.$": sample_value},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "arr": [20]}],
        msg=f"$ projection value {bson_type.value} should be accepted",
    )


REJECTION_CASES = generate_bson_rejection_test_cases(POSITIONAL_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_positional_projection_value_rejected(collection, bson_type, sample_value, spec):
    """Test $ projection errors when projection value is not a valid inclusion type."""
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$gte": 20}},
            "projection": {"arr.$": sample_value},
        },
    )
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"$ should reject {bson_type.value} as projection value",
    )
