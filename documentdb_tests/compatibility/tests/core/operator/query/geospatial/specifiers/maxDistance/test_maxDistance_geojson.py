"""Tests for $maxDistance with GeoJSON geometry ($near and $nearSphere, 2dsphere index)."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MAX,
    DOUBLE_NEGATIVE_ZERO,
    INT32_MAX,
    INT64_MAX,
)

ORIGIN = {"type": "Point", "coordinates": [0, 0]}


NEAR_GEOJSON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="filters_within_distance",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 200000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        msg="Should return only documents within $maxDistance meters",
    ),
    QueryTestCase(
        id="sorted_nearest_first",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 2000000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [10, 10]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should return results sorted by distance (nearest first)",
    ),
    QueryTestCase(
        id="boundary_inclusion_1_degree",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": 111320,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.5, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.5, 0]}},
        ],
        msg="Should include docs within ~111km (1 degree) and exclude those beyond",
    ),
    QueryTestCase(
        id="with_minDistance_annular",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 200000,
                    "$maxDistance": 500000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},  # 0m — below min
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},  # ~111km — below min
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},  # ~222km — inside ring
            {"_id": 4, "loc": {"type": "Point", "coordinates": [4, 0]}},  # ~445km — inside ring
            {"_id": 5, "loc": {"type": "Point", "coordinates": [5, 0]}},  # ~556km — above max
        ],
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [4, 0]}},
        ],
        msg="Should exclude docs below $minDistance and above $maxDistance",
    ),
    QueryTestCase(
        id="maxDistance_2000m_filters",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": 2000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.01, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.01, 0]}},
        ],
        msg="Should filter with $maxDistance 2000 meters",
    ),
    QueryTestCase(
        id="half_earth_circumference_antipodal",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [180, 0]},
                    "$maxDistance": 20100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should include antipodal point with $maxDistance > half earth circumference",
    ),
    QueryTestCase(
        id="empty_result_when_none_within",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[],
        msg="Should return empty when no documents within distance",
    ),
]


VALID_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="positive_int",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept positive integer $maxDistance",
    ),
    QueryTestCase(
        id="positive_double",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1000.5}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept positive double $maxDistance",
    ),
    QueryTestCase(
        id="int64",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": Int64(5000)}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept Int64 $maxDistance",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": Decimal128("1000.5")}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept Decimal128 $maxDistance",
    ),
    QueryTestCase(
        id="very_large_value",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 40075000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should accept very large $maxDistance (earth circumference)",
    ),
]


BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="very_small_1mm",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 0.001}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.001, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should handle very small $maxDistance (1mm)",
    ),
    QueryTestCase(
        id="very_small_1e_neg10",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1e-10}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.0001, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should handle extremely small $maxDistance (1e-10)",
    ),
    QueryTestCase(
        id="half_earth_circumference",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$maxDistance": 20037508,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [90, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [90, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should include all docs with $maxDistance = half earth circumference",
    ),
    QueryTestCase(
        id="larger_than_earth",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 50000000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, 45]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, 45]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should return all documents with $maxDistance larger than earth circumference",
    ),
    QueryTestCase(
        id="int32_max_accepted_returns_all",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": INT32_MAX}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should accept INT32_MAX as $maxDistance",
    ),
    QueryTestCase(
        id="int64_max_accepted_returns_all",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": INT64_MAX}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should accept INT64_MAX as $maxDistance",
    ),
    QueryTestCase(
        id="double_max_accepted_returns_all",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": DOUBLE_MAX}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should accept DOUBLE_MAX as $maxDistance without overflow error",
    ),
    QueryTestCase(
        id="antimeridian_crossing",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [179.5, 0]},
                    "$maxDistance": 200000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179.5, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179.5, 0]}},
        ],
        msg="Should find point across antimeridian (~1 degree apart, not 359)",
    ),
    QueryTestCase(
        id="pole_query",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 90]},
                    "$maxDistance": 200000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [90, 89]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 80]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [90, 89]}},
        ],
        msg="Should find points near pole regardless of longitude",
    ),
    QueryTestCase(
        id="exact_center_with_zero_distance",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 0}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.001, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should return document at exact center with $maxDistance 0",
    ),
    QueryTestCase(
        id="negative_zero",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": DOUBLE_NEGATIVE_ZERO}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should treat -0.0 same as 0 for $maxDistance",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1000000}}},
        doc=[],
        expected=[],
        msg="Should return empty array on empty collection (no error)",
    ),
]


NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_location_excluded",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1000000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": None},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should not match documents with null location field",
    ),
    QueryTestCase(
        id="missing_location_excluded",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1000000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "other": "value"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should not match documents with missing location field",
    ),
    QueryTestCase(
        id="all_null_or_missing",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1000000}}},
        doc=[
            {"_id": 1, "loc": None},
            {"_id": 2, "other": "value"},
        ],
        expected=[],
        msg="Should return empty when all docs have null/missing location",
    ),
]


NEARSPHERE_GEOJSON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geojson_filters_within_meters",
        filter={"loc": {"$nearSphere": {"$geometry": ORIGIN, "$maxDistance": 200000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        msg="Should filter $nearSphere GeoJSON results within $maxDistance meters",
    ),
    QueryTestCase(
        id="geojson_sorted_nearest_first",
        filter={"loc": {"$nearSphere": {"$geometry": ORIGIN, "$maxDistance": 2000000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [10, 10]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should return $nearSphere results sorted nearest first",
    ),
    QueryTestCase(
        id="geojson_with_minDistance_annular",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": ORIGIN,
                    "$minDistance": 500000,
                    "$maxDistance": 1500000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Should return $nearSphere docs in annular region",
    ),
    QueryTestCase(
        id="geojson_maxDistance_only",
        filter={"loc": {"$nearSphere": {"$geometry": ORIGIN, "$maxDistance": 500000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 2]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 2]}},
        ],
        msg="Should limit $nearSphere to nearby documents only",
    ),
]


ALL_NEAR_TESTS = NEAR_GEOJSON_TESTS + VALID_TYPE_TESTS + BOUNDARY_TESTS + NULL_MISSING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_NEAR_TESTS))
def test_maxDistance_near_geojson(collection, test):
    """Verifies $maxDistance with $near and GeoJSON geometry.

    Covers: NEAR_GEOJSON_TESTS, VALID_TYPE_TESTS, BOUNDARY_TESTS,
    NULL_MISSING_TESTS.
    """
    collection.create_index([("loc", "2dsphere")])
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NEARSPHERE_GEOJSON_TESTS))
def test_maxDistance_nearSphere_geojson(collection, test):
    """Verifies $maxDistance with $nearSphere and GeoJSON geometry."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_maxDistance_sparse_index(collection):
    """Verifies $maxDistance works with sparse 2dsphere index."""
    collection.create_index([("loc", "2dsphere")], sparse=True)
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "name": "no location field"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 200000}}},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        msg="Should work with sparse index, skipping docs without loc field",
    )


def test_maxDistance_3d_coordinates_altitude_ignored(collection):
    """Verifies $maxDistance ignores altitude (3rd coordinate)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0, 10000]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0, 0]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0, 5000]},
                        "$maxDistance": 200000,
                    }
                }
            },
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0, 10000]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0, 0]}},
        ],
        msg="Should ignore altitude — distance calculated on 2D surface only",
    )


def test_maxDistance_sort_stability_close_points(collection):
    """Verifies sort order for points at similar distances."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.001, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0.005]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 600}}},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.001, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0.005]}},
        ],
        msg="Should return all points sorted by distance",
    )
