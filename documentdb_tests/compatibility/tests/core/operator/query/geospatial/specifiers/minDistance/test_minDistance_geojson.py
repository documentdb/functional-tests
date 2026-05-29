"""Tests for $minDistance with GeoJSON geometry (2dsphere index)."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_MAX,
    DOUBLE_NEGATIVE_ZERO,
    INT32_MAX,
    INT64_MAX,
)

ORIGIN = {"type": "Point", "coordinates": [0, 0]}
DOC_AT_ORIGIN = [{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}]

EARTH_CIRCUMFERENCE_METERS = 40075017
EARTH_HALF_CIRCUMFERENCE_METERS = 20037508

# Points at known approximate distances from [0, 0]:
# [1, 0] ≈ 111km, [5, 5] ≈ 786km, [10, 10] ≈ 1568km
DOCS = [
    {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
    {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
    {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
    {"_id": 4, "loc": {"type": "Point", "coordinates": [10, 10]}},
]


NEAR_GEOJSON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="excludes_docs_closer_than_minDistance",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 200000}}},
        doc=DOCS,
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should exclude documents closer than 200km from origin",
    ),
    QueryTestCase(
        id="zero_minDistance_includes_all",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 0}}},
        doc=DOCS,
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should include all documents when $minDistance is 0",
    ),
    QueryTestCase(
        id="results_sorted_by_distance",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 100000}}},
        doc=DOCS,
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should return results sorted nearest first among those beyond minDistance",
    ),
    QueryTestCase(
        id="large_minDistance_excludes_all",
        filter={
            "loc": {"$near": {"$geometry": ORIGIN, "$minDistance": EARTH_CIRCUMFERENCE_METERS}}
        },
        doc=DOCS,
        expected=[],
        msg="Should return empty when minDistance exceeds earth circumference",
    ),
    QueryTestCase(
        id="distance_in_meters_precision",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 112000}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Should use meters for GeoJSON — 112km excludes point at ~111km",
    ),
    QueryTestCase(
        id="excludes_exact_center",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 1}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        msg="Should exclude document at exact center when minDistance > 0",
    ),
]


VALID_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="positive_int",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 1000}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept positive int $minDistance",
    ),
    QueryTestCase(
        id="positive_double",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 1000.5}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept positive double $minDistance",
    ),
    QueryTestCase(
        id="positive_int64",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": Int64(1000)}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept positive Int64 $minDistance",
    ),
    QueryTestCase(
        id="positive_decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": Decimal128("1000")}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept positive Decimal128 $minDistance",
    ),
    QueryTestCase(
        id="int32_max",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": INT32_MAX}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept INT32_MAX as $minDistance",
    ),
    QueryTestCase(
        id="int64_max",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": INT64_MAX}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept INT64_MAX as $minDistance",
    ),
    QueryTestCase(
        id="double_max",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": DOUBLE_MAX}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept DOUBLE_MAX as $minDistance",
    ),
    QueryTestCase(
        id="very_small_positive",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 1e-10}}},
        doc=DOC_AT_ORIGIN,
        expected=[],
        msg="Should accept very small positive double as $minDistance",
    ),
    QueryTestCase(
        id="negative_zero_double",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": DOUBLE_NEGATIVE_ZERO}}},
        doc=DOC_AT_ORIGIN,
        expected=DOC_AT_ORIGIN,
        msg="Should accept DOUBLE_NEGATIVE_ZERO as $minDistance (treated as 0)",
    ),
    QueryTestCase(
        id="negative_zero_decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": DECIMAL128_NEGATIVE_ZERO}}},
        doc=DOC_AT_ORIGIN,
        expected=DOC_AT_ORIGIN,
        msg="Should accept DECIMAL128_NEGATIVE_ZERO as $minDistance (treated as 0)",
    ),
]


BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="very_small_minDistance_1mm",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 0.001}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        msg="Should filter with sub-meter precision (1mm minDistance excludes exact center)",
    ),
    QueryTestCase(
        id="half_earth_circumference",
        filter={
            "loc": {"$near": {"$geometry": ORIGIN, "$minDistance": EARTH_HALF_CIRCUMFERENCE_METERS}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[],
        msg="Should return empty — antipodal point is ~20037km, within 20037.5km minDistance",
    ),
    QueryTestCase(
        id="antimeridian_crossing",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [-179.5, 0]},
                    "$minDistance": 200000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-179.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [179.5, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should correctly handle antimeridian — [179.5,0] is ~111km from [-179.5,0]",
    ),
    QueryTestCase(
        id="pole_query",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 90]},
                    "$minDistance": 1000000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 80]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 80]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should correctly calculate distance from North Pole",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 1000}}},
        doc=[],
        expected=[],
        msg="Should return empty array on empty collection without error",
    ),
]


INTERACTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="normal_annular_region",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 100000,
                    "$maxDistance": 1000000,
                }
            }
        },
        doc=DOCS,
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Should return docs in annular region (100km-1000km)",
    ),
    QueryTestCase(
        id="min_greater_than_max_empty",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 5000000,
                    "$maxDistance": 1000000,
                }
            }
        },
        doc=DOCS,
        expected=[],
        msg="Should return empty when $minDistance > $maxDistance",
    ),
    QueryTestCase(
        id="min_equals_max",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 1000000,
                    "$maxDistance": 1000000,
                }
            }
        },
        doc=DOCS,
        expected=[],
        msg="Should return empty when min equals max and no doc is at exactly that distance",
    ),
    QueryTestCase(
        id="min_zero_max_5000km",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 0,
                    "$maxDistance": 5000000,
                }
            }
        },
        doc=DOCS,
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should behave as maxDistance alone when minDistance is 0",
    ),
    QueryTestCase(
        id="min_zero_max_zero",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 0,
                    "$maxDistance": 0,
                }
            }
        },
        doc=DOCS,
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should return only exact location match when both min and max are 0",
    ),
    QueryTestCase(
        id="tight_annular_includes_one",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 700000,
                    "$maxDistance": 900000,
                }
            }
        },
        doc=DOCS,
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Should return only docs in tight annular region (700km-900km)",
    ),
]


NEARSPHERE_GEOJSON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geojson_minDistance_meters",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": ORIGIN,
                    "$minDistance": 200000,
                }
            }
        },
        doc=DOCS,
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should exclude docs closer than 200km with $nearSphere + GeoJSON",
    ),
    QueryTestCase(
        id="geojson_minDistance_zero",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": ORIGIN,
                    "$minDistance": 0,
                }
            }
        },
        doc=DOCS,
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        msg="Should include all docs when $minDistance is 0 with $nearSphere + GeoJSON",
    ),
    QueryTestCase(
        id="geojson_annular_region",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": ORIGIN,
                    "$minDistance": 500000,
                    "$maxDistance": 1000000,
                }
            }
        },
        doc=DOCS,
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Should return docs in annular region with $nearSphere + GeoJSON",
    ),
    QueryTestCase(
        id="geojson_large_minDistance_empty",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": ORIGIN,
                    "$minDistance": EARTH_CIRCUMFERENCE_METERS,
                }
            }
        },
        doc=DOCS,
        expected=[],
        msg="Should return empty when minDistance exceeds earth circumference",
    ),
]


ALL_TESTS = NEAR_GEOJSON_TESTS + VALID_VALUE_TESTS + BOUNDARY_TESTS + INTERACTION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_minDistance_near_geojson(collection, test):
    """Verifies $minDistance with $near and GeoJSON geometry."""
    collection.create_index([("loc", "2dsphere")])
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NEARSPHERE_GEOJSON_TESTS))
def test_minDistance_nearSphere_geojson(collection, test):
    """Verifies $minDistance with $nearSphere and GeoJSON Point (meters)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_minDistance_sparse_index(collection):
    """Verifies $minDistance works with sparse 2dsphere index."""
    collection.create_index([("loc", "2dsphere")], sparse=True)
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "name": "no location field"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 100000}}},
        },
    )
    assertSuccess(
        result,
        [{"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}}],
        msg="Should work with sparse index, excluding close docs and skipping missing",
    )


def test_minDistance_3d_coordinates_altitude_ignored(collection):
    """Verifies $minDistance ignores altitude (3rd coordinate)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0, 10000]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5, 0]}},
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
                        "$minDistance": 100000,
                    }
                }
            },
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5, 0]}}],
        msg="Should ignore altitude — distance calculated on 2D surface only",
    )


def test_minDistance_nested_field_path(collection):
    """Verifies $minDistance works with a nested (dotted) location field."""
    collection.create_index([("address.loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "address": {"loc": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "address": {"loc": {"type": "Point", "coordinates": [5, 5]}}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"address.loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 200000}}},
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "address": {"loc": {"type": "Point", "coordinates": [5, 5]}}}],
        msg="Should filter by $minDistance on nested field path",
    )
