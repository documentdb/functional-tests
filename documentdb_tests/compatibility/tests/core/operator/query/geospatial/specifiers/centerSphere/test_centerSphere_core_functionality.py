"""Tests for $centerSphere core functionality — containment, GeoJSON, legacy, and basic queries."""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="returns_points_within_sphere",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 10 / 6371]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.01, 0.01]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.01, 0.01]}},
        ],
        msg="Should return only points within the spherical cap",
    ),
    QueryTestCase(
        id="point_at_center_matches",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10, 20], 0.01]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10, 20]}}],
        msg="Should match point at exact center",
    ),
    QueryTestCase(
        id="no_documents_inside",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.001]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [100, 45]}},
        ],
        expected=[],
        msg="Should return empty when no documents within sphere",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[],
        expected=[],
        msg="Should return empty on empty collection without error",
    ),
    QueryTestCase(
        id="geojson_point_documents",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[-73.97, 40.77], 0.01]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-73.97, 40.77]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [100, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-73.97, 40.77]}}],
        msg="Should match GeoJSON Point documents",
    ),
    QueryTestCase(
        id="legacy_coordinate_pairs",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[-73.97, 40.77], 0.01]}}},
        doc=[
            {"_id": 1, "loc": [-73.97, 40.77]},
            {"_id": 2, "loc": [100, 0]},
        ],
        expected=[{"_id": 1, "loc": [-73.97, 40.77]}],
        msg="Should match legacy [lng, lat] coordinate pairs",
    ),
    QueryTestCase(
        id="mixed_geojson_and_legacy",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [100, 100]},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": [0, 0]},
        ],
        msg="Should match both GeoJSON and legacy documents",
    ),
    QueryTestCase(
        id="multiple_documents_same_location",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should return all documents at same location",
    ),
    QueryTestCase(
        id="radius_pi_returns_all",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], math.pi]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, 45]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, 45]}},
        ],
        msg="Should return all documents with radius = pi (entire sphere)",
    ),
    QueryTestCase(
        id="linestring_within_sphere",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "LineString",
                    "coordinates": [[0, 0], [1, 1]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "LineString",
                    "coordinates": [[0, 0], [100, 0]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
            },
        ],
        msg="Should return LineString fully within sphere",
    ),
    QueryTestCase(
        id="polygon_within_sphere",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[80, 0], [81, 0], [81, 1], [80, 1], [80, 0]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            },
        ],
        msg="Should return Polygon fully within sphere",
    ),
    QueryTestCase(
        id="polygon_intersecting_not_within",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 5 / 6371]}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                },
            },
        ],
        expected=[],
        msg="Should not return Polygon that intersects but is not fully within sphere",
    ),
    QueryTestCase(
        id="multipolygon_within_sphere",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]],
                    ],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]],
                    ],
                },
            },
        ],
        msg="Should return MultiPolygon fully within sphere",
    ),
    QueryTestCase(
        id="multipolygon_partially_outside",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 5 / 6371]}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[0, 0], [0.001, 0], [0.001, 0.001], [0, 0.001], [0, 0]]],
                        [[[80, 0], [81, 0], [81, 1], [80, 1], [80, 0]]],
                    ],
                },
            },
        ],
        expected=[],
        msg="Should not return MultiPolygon when only one polygon is within sphere",
    ),
    QueryTestCase(
        id="radius_pi_returns_all_geometry_types",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], math.pi]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [100, 45]}},
            {
                "_id": 2,
                "loc": {"type": "LineString", "coordinates": [[50, 0], [60, 10]]},
            },
            {
                "_id": 3,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[80, 0], [81, 0], [81, 1], [80, 1], [80, 0]]],
                },
            },
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [100, 45]}},
            {"_id": 2, "loc": {"type": "LineString", "coordinates": [[50, 0], [60, 10]]}},
            {
                "_id": 3,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[80, 0], [81, 0], [81, 1], [80, 1], [80, 0]]],
                },
            },
        ],
        msg="Should return all geometry types with radius = pi",
    ),
    QueryTestCase(
        id="opposite_side_small_radius_no_match",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[180, 0], 0.01]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {
                "_id": 2,
                "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
            },
        ],
        expected=[],
        msg="Should not match geometries on opposite side of earth with small radius",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_centerSphere_core_functionality(collection, test):
    """Verifies $centerSphere returns correct documents within the spherical cap."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
