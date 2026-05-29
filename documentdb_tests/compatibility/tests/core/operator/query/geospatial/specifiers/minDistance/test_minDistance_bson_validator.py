"""Tests for $minDistance BSON type validation — GeoJSON and legacy syntax.

The legacy code path returns a different error code (16893) than GeoJSON (BAD_VALUE_ERROR = 2).
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
    BAD_VALUE_ERROR,
    LEGACY_MIN_DISTANCE_NOT_NUMBER_ERROR,
)
from documentdb_tests.framework.executor import execute_command

ORIGIN = {"type": "Point", "coordinates": [0, 0]}

# --- GeoJSON (2dsphere index) ---

GEOJSON_BSON_PARAMS = [
    BsonTypeTestCase(
        id="minDistance",
        msg="$minDistance should reject non-numeric types",
        keyword="$minDistance",
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


@pytest.mark.parametrize("operator", ["$near", "$nearSphere"])
@pytest.mark.parametrize("bson_type,sample_value,spec", GEOJSON_REJECTION)
def test_minDistance_geojson_bson_rejected(collection, operator, bson_type, sample_value, spec):
    """Verifies $minDistance rejects invalid BSON types (GeoJSON)."""
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
def test_minDistance_geojson_bson_accepted(collection, operator, bson_type, sample_value, spec):
    """Verifies $minDistance accepts valid BSON types (GeoJSON)."""
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
        id="minDistance_legacy",
        msg="$minDistance should reject non-numeric types (legacy)",
        keyword="$minDistance",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 0.0,
            BsonType.INT: 0,
            BsonType.LONG: Int64(0),
            BsonType.DECIMAL: Decimal128("0"),
        },
        default_error_code=LEGACY_MIN_DISTANCE_NOT_NUMBER_ERROR,
    ),
]

LEGACY_REJECTION = generate_bson_rejection_test_cases(LEGACY_BSON_PARAMS)
LEGACY_ACCEPTANCE = generate_bson_acceptance_test_cases(LEGACY_BSON_PARAMS)


@pytest.mark.parametrize("operator", ["$near", "$nearSphere"])
@pytest.mark.parametrize("bson_type,sample_value,spec", LEGACY_REJECTION)
def test_minDistance_legacy_bson_rejected(collection, operator, bson_type, sample_value, spec):
    """Verifies $minDistance rejects invalid BSON types (legacy)."""
    collection.create_index([("loc", "2d")])
    filt = {"loc": {operator: [0, 0], spec.keyword: sample_value}}
    result = execute_command(collection, {"find": collection.name, "filter": filt})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("operator", ["$near", "$nearSphere"])
@pytest.mark.parametrize("bson_type,sample_value,spec", LEGACY_ACCEPTANCE)
def test_minDistance_legacy_bson_accepted(collection, operator, bson_type, sample_value, spec):
    """Verifies $minDistance accepts valid BSON types (legacy)."""
    collection.create_index([("loc", "2d")])
    collection.insert_one({"_id": 1, "loc": [0, 0]})
    filt = {"loc": {operator: [0, 0], spec.keyword: sample_value}}
    result = execute_command(collection, {"find": collection.name, "filter": filt})
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}],
        msg=f"{spec.keyword} should accept {bson_type.value} (legacy)",
    )
