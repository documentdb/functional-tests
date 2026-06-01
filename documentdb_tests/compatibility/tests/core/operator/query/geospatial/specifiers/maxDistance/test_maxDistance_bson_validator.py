"""Tests for $maxDistance BSON type validation — GeoJSON and legacy syntax.

The legacy code path returns a different error code (16895) than GeoJSON (BAD_VALUE_ERROR = 2).
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    LEGACY_MAX_DISTANCE_NOT_NUMBER_ERROR,
)
from documentdb_tests.framework.executor import execute_command

ORIGIN = {"type": "Point", "coordinates": [0, 0]}

# --- GeoJSON (2dsphere index) ---

GEOJSON_BSON_PARAMS = [
    BsonTypeTestCase(
        id="maxDistance",
        msg="$maxDistance should reject non-numeric types",
        keyword="$maxDistance",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=BAD_VALUE_ERROR,
    ),
]

GEOJSON_REJECTION = generate_bson_rejection_test_cases(GEOJSON_BSON_PARAMS)
GEOJSON_ACCEPTANCE = generate_bson_acceptance_test_cases(GEOJSON_BSON_PARAMS)


@pytest.mark.parametrize("operator", ["$near", "$nearSphere"])
@pytest.mark.parametrize("bson_type,sample_value,spec", GEOJSON_REJECTION)
def test_maxDistance_geojson_bson_rejected(collection, operator, bson_type, sample_value, spec):
    """Verifies $maxDistance rejects invalid BSON types (GeoJSON)."""
    collection.create_index([("loc", "2dsphere")])
    filt = {
        "loc": {
            operator: {
                "$geometry": ORIGIN,
                spec.keyword: sample_value,
            }
        }
    }
    result = execute_command(collection, {"find": collection.name, "filter": filt})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("operator", ["$near", "$nearSphere"])
@pytest.mark.parametrize("bson_type,sample_value,spec", GEOJSON_ACCEPTANCE)
def test_maxDistance_geojson_bson_accepted(collection, operator, bson_type, sample_value, spec):
    """Verifies $maxDistance accepts valid BSON types (GeoJSON)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_one({"_id": 1, "loc": ORIGIN})
    filt = {
        "loc": {
            operator: {
                "$geometry": ORIGIN,
                spec.keyword: sample_value,
            }
        }
    }
    result = execute_command(collection, {"find": collection.name, "filter": filt})
    assertSuccess(
        result,
        [{"_id": 1, "loc": ORIGIN}],
        msg=f"{spec.keyword} should accept {bson_type.value}",
    )


# --- Legacy (2d index) ---

LEGACY_BSON_PARAMS = [
    BsonTypeTestCase(
        id="maxDistance_legacy",
        msg="$maxDistance should reject non-numeric types (legacy)",
        keyword="$maxDistance",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=LEGACY_MAX_DISTANCE_NOT_NUMBER_ERROR,
    ),
]

LEGACY_REJECTION = generate_bson_rejection_test_cases(LEGACY_BSON_PARAMS)
LEGACY_ACCEPTANCE = generate_bson_acceptance_test_cases(LEGACY_BSON_PARAMS)


@pytest.mark.parametrize("operator", ["$near", "$nearSphere"])
@pytest.mark.parametrize("bson_type,sample_value,spec", LEGACY_REJECTION)
def test_maxDistance_legacy_bson_rejected(collection, operator, bson_type, sample_value, spec):
    """Verifies $maxDistance rejects invalid BSON types (legacy)."""
    collection.create_index([("loc", "2d")])
    filt = {"loc": {operator: [0, 0], spec.keyword: sample_value}}
    result = execute_command(collection, {"find": collection.name, "filter": filt})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("operator", ["$near", "$nearSphere"])
@pytest.mark.parametrize("bson_type,sample_value,spec", LEGACY_ACCEPTANCE)
def test_maxDistance_legacy_bson_accepted(collection, operator, bson_type, sample_value, spec):
    """Verifies $maxDistance accepts valid BSON types (legacy)."""
    collection.create_index([("loc", "2d")])
    collection.insert_one({"_id": 1, "loc": [0, 0]})
    filt = {"loc": {operator: [0, 0], spec.keyword: sample_value}}
    result = execute_command(collection, {"find": collection.name, "filter": filt})
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}],
        msg=f"{spec.keyword} should accept {bson_type.value} (legacy)",
    )
