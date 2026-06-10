"""
Tests for $geoIntersects BSON type validation of the $geometry argument and its fields.

Verifies that $geoIntersects rejects invalid BSON types for $geometry, its "type"
field, and its "coordinates" field with expected error codes.
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

VALID_POLYGON_COORDS = [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]]

GEOINTERSECTS_PARAMS = [
    BsonTypeTestCase(
        id="geometry",
        msg="$geometry should reject non-object types",
        keyword="$geometry",
        valid_types=[BsonType.OBJECT],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={BsonType.OBJECT: {"type": "Polygon", "coordinates": VALID_POLYGON_COORDS}},
    ),
    BsonTypeTestCase(
        id="geometry_type",
        msg="$geometry 'type' field should reject non-string types",
        keyword="type",
        valid_types=[BsonType.STRING],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={BsonType.STRING: "Polygon"},
    ),
    BsonTypeTestCase(
        id="geometry_coordinates",
        msg="$geometry 'coordinates' field should reject non-array types",
        keyword="coordinates",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={BsonType.ARRAY: VALID_POLYGON_COORDS},
    ),
    BsonTypeTestCase(
        id="geometry_crs",
        msg="$geometry 'crs' field should reject non-object types",
        keyword="crs",
        valid_types=[BsonType.OBJECT],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        valid_inputs={
            BsonType.OBJECT: {
                "type": "name",
                "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
            }
        },
    ),
]


def _build_filter(spec, sample_value):
    """Build the $geoIntersects filter based on which keyword is being tested."""
    if spec.keyword == "$geometry":
        return {"loc": {"$geoIntersects": {"$geometry": sample_value}}}
    if spec.keyword == "type":
        geometry = {"type": sample_value, "coordinates": VALID_POLYGON_COORDS}
    elif spec.keyword == "crs":
        geometry = {"type": "Polygon", "coordinates": VALID_POLYGON_COORDS, "crs": sample_value}
    else:
        geometry = {"type": "Polygon", "coordinates": sample_value}
    return {"loc": {"$geoIntersects": {"$geometry": geometry}}}


TEST_CASES = generate_bson_rejection_test_cases(GEOINTERSECTS_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TEST_CASES)
def test_geoIntersects_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $geoIntersects rejects invalid BSON types."""
    result = execute_command(
        collection, {"find": collection.name, "filter": _build_filter(spec, sample_value)}
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(GEOINTERSECTS_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_geoIntersects_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $geoIntersects accepts valid BSON types."""
    collection.insert_many(spec.expected)
    result = execute_command(
        collection, {"find": collection.name, "filter": _build_filter(spec, sample_value)}
    )
    assertSuccess(result, spec.expected, msg=f"{spec.keyword} should accept {bson_type.value}")
