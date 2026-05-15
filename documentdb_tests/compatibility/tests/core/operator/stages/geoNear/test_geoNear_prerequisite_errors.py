"""Tests for $geoNear prerequisite errors."""

from __future__ import annotations

import pytest
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INDEX_NOT_FOUND_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
    POINT_NOT_IN_INTERVAL_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [GeoJSON Type Case Sensitivity]: the GeoJSON type field is
# case-sensitive; lowercase variants such as "point" are rejected.
GEONEAR_GEOJSON_TYPE_CASE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geojson_lowercase_point_rejected",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg='$geoNear with lowercase "point" type should be rejected',
    ),
]

# Property [Legacy Near Point Range - 2d Index]: legacy coordinate values
# with a 2d index must be in [-180, 180]; values outside are rejected.
GEONEAR_LEGACY_2D_RANGE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "legacy_2d_lon_above_180",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [181, 0], "distanceField": "dist", "spherical": False}}],
        error_code=POINT_NOT_IN_INTERVAL_ERROR,
        msg="$geoNear with legacy lon=181 and 2d index should fail",
    ),
    StageTestCase(
        "legacy_2d_lon_below_neg180",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [-181, 0], "distanceField": "dist", "spherical": False}}],
        error_code=POINT_NOT_IN_INTERVAL_ERROR,
        msg="$geoNear with legacy lon=-181 and 2d index should fail",
    ),
]

# Property [Legacy Near Point Range - 2dsphere]: legacy coordinates with a
# 2dsphere index and spherical=true must have lon in [-180, 180] and lat in
# [-90, 90]; values outside are rejected.
GEONEAR_LEGACY_2DSPHERE_RANGE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "legacy_2dsphere_lon_above_180",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [181, 0], "distanceField": "dist", "spherical": True}}],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with legacy lon=181 and 2dsphere+spherical should fail",
    ),
    StageTestCase(
        "legacy_2dsphere_lat_above_90",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [0, 91], "distanceField": "dist", "spherical": True}}],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with legacy lat=91 and 2dsphere+spherical should fail",
    ),
]

# Property [No Geospatial Index]: $geoNear requires a geospatial index on
# the collection; without one, it fails with an index-not-found error.
GEONEAR_NO_GEO_INDEX_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "no_geo_index",
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="$geoNear with no geospatial index should fail",
    ),
]

# Property [No Collection]: $geoNear on a nonexistent collection fails with a
# namespace-not-found error.
GEONEAR_NO_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "no_collection",
        docs=None,
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="$geoNear on a nonexistent collection should fail",
    ),
]

# Property [Ambiguous Same-Type Indexes]: when multiple geospatial indexes of
# the same type exist and key is not specified, $geoNear fails with an
# index-not-found error.
GEONEAR_AMBIGUOUS_INDEX_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multiple_2dsphere_no_key",
        indexes=[IndexModel([("loc", "2dsphere")]), IndexModel([("loc2", "2dsphere")])],
        docs=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "loc2": {"type": "Point", "coordinates": [1, 0]},
            },
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="$geoNear with multiple 2dsphere indexes and no key should fail",
    ),
]

# Property [Index-Near Type Mismatch]: $geoNear fails when the near point
# type is incompatible with the available geospatial index.
GEONEAR_INDEX_MISMATCH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "legacy_near_2dsphere_spherical_false",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [0, 0], "distanceField": "dist", "spherical": False}}],
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="$geoNear with legacy near, 2dsphere index, and spherical=false should fail",
    ),
    StageTestCase(
        "geojson_near_2d_index",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="$geoNear with GeoJSON near and 2d index should fail",
    ),
    StageTestCase(
        "key_non_geo_indexed_field",
        indexes=[IndexModel([("loc", "2dsphere")]), IndexModel([("name", 1)])],
        docs=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "name": "test",
            },
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "name",
                }
            }
        ],
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="$geoNear with key pointing to a non-geo-indexed field should fail",
    ),
]

GEONEAR_PREREQUISITE_ERROR_TESTS = (
    GEONEAR_GEOJSON_TYPE_CASE_ERROR_TESTS
    + GEONEAR_LEGACY_2D_RANGE_ERROR_TESTS
    + GEONEAR_LEGACY_2DSPHERE_RANGE_ERROR_TESTS
    + GEONEAR_NO_GEO_INDEX_ERROR_TESTS
    + GEONEAR_NO_COLLECTION_ERROR_TESTS
    + GEONEAR_AMBIGUOUS_INDEX_ERROR_TESTS
    + GEONEAR_INDEX_MISMATCH_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_PREREQUISITE_ERROR_TESTS))
def test_geoNear_prerequisite_errors(collection, test_case: StageTestCase):
    """Test $geoNear prerequisite errors."""
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
