"""Tests for $geometry context-specific behavior —
$geoWithin, $geoIntersects, $near, $nearSphere."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POLYGON_COORDS = [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]


GEOWITHIN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geoWithin_polygon",
        filter={
            "loc": {"$geoWithin": {"$geometry": {"type": "Polygon", "coordinates": POLYGON_COORDS}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}}],
        msg="Should find documents within polygon",
    ),
    QueryTestCase(
        id="geoWithin_multipolygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            POLYGON_COORDS,
                            [[[10, 10], [12, 10], [12, 12], [10, 12], [10, 10]]],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [11, 11]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [11, 11]}},
        ],
        msg="Should find documents within any polygon in MultiPolygon",
    ),
]


GEOINTERSECTS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geoIntersects_point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [1, 1]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}}],
        msg="Should find documents at exact point with $geoIntersects",
    ),
    QueryTestCase(
        id="geoIntersects_linestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[0, 0], [2, 2]]}
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should find documents intersecting LineString",
    ),
    QueryTestCase(
        id="geoIntersects_polygon",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Polygon", "coordinates": POLYGON_COORDS}}
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}}],
        msg="Should find documents intersecting Polygon",
    ),
]


@pytest.mark.parametrize("test", pytest_params(GEOWITHIN_TESTS))
def test_geometry_geoWithin(collection, test):
    """Verifies $geometry works correctly with $geoWithin operator."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(GEOINTERSECTS_TESTS))
def test_geometry_geoIntersects(collection, test):
    """Verifies $geometry works correctly with $geoIntersects operator."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


NEAR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_point_sorted_by_distance",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 0]}},
        ],
        msg="Should return documents sorted by distance from query point",
    ),
    QueryTestCase(
        id="nearSphere_point_sorted_by_distance",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 0]}},
        ],
        msg="Should return documents sorted by spherical distance",
    ),
    QueryTestCase(
        id="near_with_maxDistance",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": 200000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        msg="Should limit results to within $maxDistance meters",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NEAR_TESTS))
def test_geometry_near(collection, test):
    """Verifies $near/$nearSphere with $geometry Point behavior."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
