"""Tests for $geoNear near parameter type rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, ObjectId, Regex, Timestamp
from bson.decimal128 import Decimal128
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    GEO_NEAR_NEAR_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Near Type Rejection - Non-Geo Types]: $geoNear rejects near values
# that are not an array or object.
GEONEAR_NEAR_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_null",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": None, "distanceField": "dist", "spherical": True}}],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with null near should fail",
    ),
    StageTestCase(
        "near_bool",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": True, "distanceField": "dist", "spherical": True}}],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with bool near should fail",
    ),
    StageTestCase(
        "near_int",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": 42, "distanceField": "dist", "spherical": True}}],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with int near should fail",
    ),
    StageTestCase(
        "near_int64",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": Int64(1), "distanceField": "dist", "spherical": True}}],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with Int64 near should fail",
    ),
    StageTestCase(
        "near_double",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": 3.14, "distanceField": "dist", "spherical": True}}],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with double near should fail",
    ),
    StageTestCase(
        "near_decimal128",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {"$geoNear": {"near": Decimal128("1"), "distanceField": "dist", "spherical": True}}
        ],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with Decimal128 near should fail",
    ),
    StageTestCase(
        "near_string",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": "hello", "distanceField": "dist", "spherical": True}}],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with string near should fail",
    ),
    StageTestCase(
        "near_objectid",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": ObjectId("000000000000000000000001"),
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with ObjectId near should fail",
    ),
    StageTestCase(
        "near_datetime",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with datetime near should fail",
    ),
    StageTestCase(
        "near_timestamp",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": Timestamp(1, 1),
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with Timestamp near should fail",
    ),
    StageTestCase(
        "near_binary",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": Binary(b"\x01"),
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with Binary near should fail",
    ),
    StageTestCase(
        "near_regex",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": Regex("^a"),
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_NEAR_TYPE_ERROR,
        msg="$geoNear with Regex near should fail",
    ),
]

# Property [Near Type Rejection - Invalid Arrays and Coordinates]: arrays with
# fewer than 2 or more than 3 elements and GeoJSON coordinates containing NaN
# or Infinity are rejected as invalid near arguments.
GEONEAR_NEAR_INVALID_ARRAY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_empty_array",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": [], "distanceField": "dist", "spherical": True}}],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with empty array near should fail",
    ),
    StageTestCase(
        "near_single_element_array",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": [1], "distanceField": "dist", "spherical": True}}],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with 1-element array near should fail",
    ),
    StageTestCase(
        "near_four_element_array",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": {"near": [1, 2, 3, 4], "distanceField": "dist", "spherical": True}}],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with 4-element array near should fail",
    ),
    StageTestCase(
        "near_geojson_nan_lon",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [FLOAT_NAN, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with NaN in GeoJSON lon should fail",
    ),
    StageTestCase(
        "near_geojson_nan_lat",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, FLOAT_NAN]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with NaN in GeoJSON lat should fail",
    ),
    StageTestCase(
        "near_geojson_infinity_lon",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [FLOAT_INFINITY, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with Infinity in GeoJSON lon should fail",
    ),
    StageTestCase(
        "near_geojson_neg_infinity_lat",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, FLOAT_NEGATIVE_INFINITY]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with -Infinity in GeoJSON lat should fail",
    ),
    StageTestCase(
        "near_legacy_array_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {"$geoNear": {"near": [FLOAT_NAN, 0], "distanceField": "dist", "spherical": True}}
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with NaN in legacy array near should fail",
    ),
    StageTestCase(
        "near_legacy_array_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": [FLOAT_INFINITY, 0],
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with Infinity in legacy array near should fail",
    ),
    StageTestCase(
        "near_legacy_array_decimal128_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": [DECIMAL128_NAN, DECIMAL128_ZERO],
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with Decimal128 NaN in legacy array near should fail",
    ),
    StageTestCase(
        "near_legacy_array_decimal128_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": [DECIMAL128_INFINITY, DECIMAL128_ZERO],
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with Decimal128 Infinity in legacy array near should fail",
    ),
    StageTestCase(
        "near_geojson_decimal128_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [DECIMAL128_NAN, DECIMAL128_ZERO],
                    },
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with Decimal128 NaN in GeoJSON coordinates should fail",
    ),
    StageTestCase(
        "near_geojson_decimal128_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [DECIMAL128_INFINITY, DECIMAL128_ZERO],
                    },
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with Decimal128 Infinity in GeoJSON coordinates should fail",
    ),
]

GEONEAR_NEAR_TYPE_ERROR_TESTS_ALL = (
    GEONEAR_NEAR_TYPE_ERROR_TESTS + GEONEAR_NEAR_INVALID_ARRAY_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_NEAR_TYPE_ERROR_TESTS_ALL))
def test_geoNear_near_type_errors(collection, test_case: StageTestCase):
    """Test $geoNear near parameter type rejection."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
