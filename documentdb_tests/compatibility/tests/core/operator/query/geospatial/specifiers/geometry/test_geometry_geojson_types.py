"""Tests for $geometry valid GeoJSON type coverage — valid types and coordinate types."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Valid GeoJSON types ---

VALID_GEOJSON_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept Point type",
    ),
    QueryTestCase(
        id="linestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1], [2, 2]]}
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}}],
        msg="Should accept LineString type",
    ),
    QueryTestCase(
        id="linestring_two_points",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept LineString with minimum 2 points",
    ),
    QueryTestCase(
        id="polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should accept Polygon type",
    ),
    QueryTestCase(
        id="multipoint",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "MultiPoint", "coordinates": [[0, 0], [1, 1]]}
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept MultiPoint type",
    ),
    QueryTestCase(
        id="multilinestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiLineString",
                        "coordinates": [[[0, 0], [1, 1]], [[2, 2], [3, 3]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept MultiLineString type",
    ),
    QueryTestCase(
        id="multipolygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                            [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]],
                        ],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should accept MultiPolygon type",
    ),
]


# --- Valid coordinate types ---

VALID_COORDINATE_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="coordinates_as_int",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [10, 20]}}}
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}}],
        msg="Should accept int coordinates",
    ),
    QueryTestCase(
        id="coordinates_as_long",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [Int64(10), Int64(20)]}
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}}],
        msg="Should accept long coordinates",
    ),
    QueryTestCase(
        id="coordinates_as_double",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [10.5, 20.5]}}}
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10.5, 20.5]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10.5, 20.5]}}],
        msg="Should accept double coordinates",
    ),
    QueryTestCase(
        id="coordinates_as_decimal128",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [Decimal128("10.5"), Decimal128("20.5")],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10.5, 20.5]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10.5, 20.5]}}],
        msg="Should accept Decimal128 coordinates",
    ),
    QueryTestCase(
        id="point_three_coordinates",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [10, 20, 30]}}}
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}}],
        msg="Should accept Point with 3 coordinates (altitude ignored)",
    ),
]

ALL_TESTS = VALID_GEOJSON_TYPE_TESTS + VALID_COORDINATE_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geometry_geojson_types(collection, test):
    """Verifies $geometry accepts all valid GeoJSON geometry types
    and numeric coordinate types."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
