"""
Tests for $geoWithin BSON type validation of shape operator arguments.

Verifies that each $geoWithin shape operator rejects invalid BSON types for its
value with expected error codes and accepts valid BSON types without error.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command

GEOWITHIN_PARAMS = [
    BsonTypeTestCase(
        id="geometry",
        msg="$geometry should reject non-object types",
        keyword="$geometry",
        valid_types=[BsonType.OBJECT],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={
            BsonType.OBJECT: {
                "type": "Polygon",
                "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
            }
        },
    ),
    BsonTypeTestCase(
        id="box",
        msg="$box should reject non-array types and empty array",
        keyword="$box",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={BsonType.ARRAY: [[-10, -10], [10, 10]]},
    ),
    BsonTypeTestCase(
        id="polygon",
        msg="$polygon should reject non-array types and empty array",
        keyword="$polygon",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={BsonType.ARRAY: [[-10, -10], [10, -10], [10, 10], [-10, 10]]},
    ),
    BsonTypeTestCase(
        id="center",
        msg="$center should reject non-array types and empty array",
        keyword="$center",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={BsonType.ARRAY: [[0, 0], 10]},
    ),
    BsonTypeTestCase(
        id="centerSphere",
        msg="$centerSphere should reject non-array types and empty array",
        keyword="$centerSphere",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={BsonType.ARRAY: [[0, 0], 0.5]},
    ),
]

TEST_CASES = generate_bson_rejection_test_cases(GEOWITHIN_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    TEST_CASES,
)
def test_geoWithin_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $geoWithin shape operators reject invalid BSON types."""
    query_filter = {"loc": {"$geoWithin": {spec.keyword: sample_value}}}
    result = execute_command(collection, {"find": collection.name, "filter": query_filter})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(GEOWITHIN_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    ACCEPTANCE_CASES,
)
def test_geoWithin_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $geoWithin shape operators accept valid BSON types and return matching docs."""
    collection.insert_many(spec.expected)
    query_filter = {"loc": {"$geoWithin": {spec.keyword: sample_value}}}
    result = execute_command(collection, {"find": collection.name, "filter": query_filter})
    assertSuccess(result, spec.expected, msg=f"{spec.keyword} should accept {bson_type.value}")
