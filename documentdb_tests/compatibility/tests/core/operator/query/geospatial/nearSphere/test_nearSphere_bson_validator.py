"""
Tests for $nearSphere BSON type validation.

Verifies that $nearSphere parameters reject invalid BSON types and accept valid ones.
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

GEOJSON_BSON_PARAMS = [
    BsonTypeTestCase(
        id="geometry",
        msg="$geometry should reject non-object types",
        keyword="$geometry",
        valid_types=[BsonType.OBJECT],
        valid_inputs={
            BsonType.OBJECT: {"type": "Point", "coordinates": [0, 0]},
        },
        default_error_code=BAD_VALUE_ERROR,
    ),
    BsonTypeTestCase(
        id="coordinates",
        msg="coordinates should reject non-numeric element types",
        keyword="coordinates",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 0.0,
            BsonType.INT: 0,
            BsonType.LONG: Int64(0),
            BsonType.DECIMAL: Decimal128("0"),
        },
        default_error_code=BAD_VALUE_ERROR,
    ),
]

GEOJSON_REJECTION = generate_bson_rejection_test_cases(GEOJSON_BSON_PARAMS)
GEOJSON_ACCEPTANCE = generate_bson_acceptance_test_cases(GEOJSON_BSON_PARAMS)


def _build_geojson_filter(spec, sample_value):
    """Build GeoJSON $nearSphere filter."""
    if spec.keyword == "coordinates":
        return {
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [sample_value, sample_value],
                    }
                }
            }
        }
    return {"loc": {"$nearSphere": {"$geometry": sample_value}}}


@pytest.mark.parametrize("bson_type,sample_value,spec", GEOJSON_REJECTION)
def test_nearSphere_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $nearSphere rejects invalid BSON types."""
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": _build_geojson_filter(spec, sample_value)},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", GEOJSON_ACCEPTANCE)
def test_nearSphere_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $nearSphere accepts valid BSON types."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(
        collection,
        {"find": collection.name, "filter": _build_geojson_filter(spec, sample_value)},
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg=f"{spec.keyword} should accept {bson_type.value}",
    )
