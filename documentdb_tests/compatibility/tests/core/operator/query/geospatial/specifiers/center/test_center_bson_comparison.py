"""
Tests for $center BSON type comparison.

Verifies that $center coordinate and radius values reject invalid BSON types with expected
error codes and accept valid numeric BSON types without error.
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
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command

CENTER_COORDINATE_PARAMS = [
    BsonTypeTestCase(
        id="center_coordinate",
        msg="$center coordinates should reject non-numeric types",
        keyword="$center",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=BAD_VALUE_ERROR,
        valid_inputs={
            BsonType.DOUBLE: 10.5,
            BsonType.INT: 10,
            BsonType.LONG: Int64(10),
            BsonType.DECIMAL: Decimal128("10"),
        },
    ),
]

CENTER_RADIUS_PARAMS = [
    BsonTypeTestCase(
        id="center_radius",
        msg="$center radius should reject non-numeric types",
        keyword="$center",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=BAD_VALUE_ERROR,
        valid_inputs={
            BsonType.DOUBLE: 10.5,
            BsonType.INT: 10,
            BsonType.LONG: Int64(10),
            BsonType.DECIMAL: Decimal128("10"),
        },
    ),
]

COORDINATE_REJECTION_CASES = generate_bson_rejection_test_cases(CENTER_COORDINATE_PARAMS)
RADIUS_REJECTION_CASES = generate_bson_rejection_test_cases(CENTER_RADIUS_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    COORDINATE_REJECTION_CASES,
)
def test_center_coordinate_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $center rejects invalid BSON types as coordinate values."""
    query = {"loc": {"$geoWithin": {"$center": [[sample_value, sample_value], 10]}}}
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    RADIUS_REJECTION_CASES,
)
def test_center_radius_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $center rejects invalid BSON types as radius value."""
    query = {"loc": {"$geoWithin": {"$center": [[0, 0], sample_value]}}}
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


COORDINATE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(CENTER_COORDINATE_PARAMS)
RADIUS_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(CENTER_RADIUS_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    COORDINATE_ACCEPTANCE_CASES,
)
def test_center_coordinate_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $center accepts valid numeric BSON types as coordinate values."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [12, 8]},
            {"_id": 2, "loc": [100, 100]},
        ]
    )
    query = {"loc": {"$geoWithin": {"$center": [[sample_value, sample_value], 50]}}}
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertSuccess(result, [{"_id": 1, "loc": [12, 8]}], ignore_doc_order=True)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    RADIUS_ACCEPTANCE_CASES,
)
def test_center_radius_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $center accepts valid numeric BSON types as radius value."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [-30, 25]},
            {"_id": 2, "loc": [100, 100]},
        ]
    )
    query = {"loc": {"$geoWithin": {"$center": [[-28, 22], sample_value]}}}
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertSuccess(result, [{"_id": 1, "loc": [-30, 25]}], ignore_doc_order=True)
