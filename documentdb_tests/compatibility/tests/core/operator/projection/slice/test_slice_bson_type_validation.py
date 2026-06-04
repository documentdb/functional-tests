"""
Tests for $slice projection BSON type validation.

Verifies that $slice rejects invalid BSON types for its value with expected
error codes and accepts valid BSON types (int, long, double, decimal, array).
Also validates types within the [skip, limit] array form.
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
    EXPRESSION_ARITY_ERROR,
    SLICE_INVALID_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command

SLICE_PARAMS = [
    BsonTypeTestCase(
        id="slice_value",
        msg="$slice should reject non-numeric and non-array types",
        keyword="$slice",
        valid_types=[
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.ARRAY,
        ],
        default_error_code=EXPRESSION_ARITY_ERROR,
        expected=[{"_id": 1, "arr": [1, 2]}],
        valid_inputs={
            BsonType.INT: 2,
            BsonType.LONG: Int64(2),
            BsonType.DOUBLE: 2.0,
            BsonType.DECIMAL: Decimal128("2"),
            BsonType.ARRAY: [0, 2],
        },
    ),
    BsonTypeTestCase(
        id="slice_array_element",
        msg="$slice [skip, limit] should reject non-numeric, non-null, non-array types",
        keyword="$slice",
        valid_types=[
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
        ],
        default_error_code=SLICE_INVALID_ARGUMENT_ERROR,
        expected=[{"_id": 1, "arr": [2]}],
        valid_inputs={
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DOUBLE: 1.0,
            BsonType.DECIMAL: Decimal128("1"),
        },
        # Skip testing failure test cases in the following:
        # NULL - returns null field instead of error
        # ARRAY - triggers expression-form fallthrough
        # Both are tested in test_slice_projection_behavior.py.
        skip_rejection_types=[BsonType.NULL, BsonType.ARRAY],
    ),
]


def build_slice_projection(sample_value, spec):
    """Build $slice projection for single-value or array form."""
    if spec.id == "slice_array_element":
        return {"arr": {"$slice": [sample_value, sample_value]}}
    return {"arr": {"$slice": sample_value}}


TEST_CASES = generate_bson_rejection_test_cases(SLICE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TEST_CASES)
def test_slice_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $slice projection rejects invalid BSON types."""
    collection.insert_many([{"_id": 1, "arr": [1, 2, 3, 4, 5]}])
    result = execute_command(
        collection,
        {"find": collection.name, "projection": build_slice_projection(sample_value, spec)},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SLICE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_slice_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $slice projection accepts valid BSON types."""
    collection.insert_many([{"_id": 1, "arr": [1, 2, 3, 4, 5]}])
    result = execute_command(
        collection,
        {"find": collection.name, "projection": build_slice_projection(sample_value, spec)},
    )
    assertSuccess(result, spec.expected, msg=f"$slice should accept {bson_type.value}")
