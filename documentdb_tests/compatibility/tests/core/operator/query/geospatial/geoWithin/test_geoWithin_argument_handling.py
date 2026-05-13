"""
Tests for $geoWithin argument handling, geometry formats, null/missing fields, and document types.

Field lookup / dotted-path tests live in test_geoWithin_field_lookup.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Standard polygon for reuse in tests
POLYGON = {
    "$geometry": {
        "type": "Polygon",
        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
    }
}


ARGUMENT_HANDLING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geometry_polygon_single_ring",
        filter={"loc": {"$geoWithin": POLYGON}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geometry GeoJSON Polygon single ring should return matching docs",
    ),
    QueryTestCase(
        id="geometry_polygon_with_hole",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]],
                            [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}}],
        msg="Polygon with hole should exclude points in hole",
    ),
    QueryTestCase(
        id="geometry_multipolygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                            [[[15, 15], [25, 15], [25, 25], [15, 25], [15, 15]]],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [20, 20]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        msg="MultiPolygon should match points in either polygon",
    ),
    QueryTestCase(
        id="geometry_polygon_with_strictwinding_crs",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                        "crs": {
                            "type": "name",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Polygon with strictwinding CRS should behave like default for small polygon",
    ),
    QueryTestCase(
        id="geometry_polygon_with_strictwinding_crs_clockwise",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [-10, 10], [10, 10], [10, -10], [-10, -10]]],
                        "crs": {
                            "type": "name",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}}],
        msg="Clockwise polygon with strictwinding CRS should match complement",
    ),
    QueryTestCase(
        id="geometry_polygon_with_epsg4326_crs",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                        "crs": {
                            "type": "name",
                            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
                        },
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Polygon with standard CRS84 (EPSG:4326) CRS should match points inside",
    ),
]


NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_field_no_match",
        filter={"loc": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "loc": None}, {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Null location field should not match",
    ),
    QueryTestCase(
        id="missing_field_no_match",
        filter={"loc": {"$geoWithin": POLYGON}},
        doc=[
            {"_id": 1, "other": "value"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Missing location field should not match",
    ),
]


DOCUMENT_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="unsorted_results",
        filter={"loc": {"$geoWithin": POLYGON}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [9, 9]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [9, 9]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Results are not sorted by distance — all within should be returned",
    ),
    QueryTestCase(
        id="array_of_geojson_points",
        filter={"locs": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "locs": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [5, 5]},
                ],
            },
            {
                "_id": 2,
                "locs": [
                    {"type": "Point", "coordinates": [50, 50]},
                    {"type": "Point", "coordinates": [60, 60]},
                ],
            },
        ],
        expected=[
            {
                "_id": 1,
                "locs": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [5, 5]},
                ],
            }
        ],
        msg="Array of GeoJSON Points should match if any element is within",
    ),
    QueryTestCase(
        id="array_of_legacy_coords",
        filter={"locs": {"$geoWithin": {"$box": [[-10, -10], [10, 10]]}}},
        doc=[{"_id": 1, "locs": [[0, 0], [5, 5]]}, {"_id": 2, "locs": [[50, 50], [60, 60]]}],
        expected=[{"_id": 1, "locs": [[0, 0], [5, 5]]}],
        msg="Array of legacy coordinate pairs should match",
    ),
    QueryTestCase(
        id="array_of_linestrings",
        filter={"routes": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "routes": [
                    {"type": "LineString", "coordinates": [[0, 0], [5, 5]]},
                    {"type": "LineString", "coordinates": [[0, 0], [50, 50]]},
                ],
            },
            {
                "_id": 2,
                "routes": [
                    {"type": "LineString", "coordinates": [[50, 50], [60, 60]]},
                    {"type": "LineString", "coordinates": [[0, 0], [50, 50]]},
                ],
            },
        ],
        expected=[
            {
                "_id": 1,
                "routes": [
                    {"type": "LineString", "coordinates": [[0, 0], [5, 5]]},
                    {"type": "LineString", "coordinates": [[0, 0], [50, 50]]},
                ],
            }
        ],
        msg="Array of LineStrings should match if any element is entirely within",
    ),
    QueryTestCase(
        id="array_of_polygons",
        filter={"coverage_areas": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "coverage_areas": [
                    {
                        "type": "Polygon",
                        "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                    },
                    {
                        "type": "Polygon",
                        "coordinates": [[[-50, -50], [50, -50], [50, 50], [-50, 50], [-50, -50]]],
                    },
                ],
            },
            {
                "_id": 2,
                "coverage_areas": [
                    {
                        "type": "Polygon",
                        "coordinates": [[[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]]],
                    },
                    {
                        "type": "Polygon",
                        "coordinates": [[[40, 40], [50, 40], [50, 50], [40, 50], [40, 40]]],
                    },
                ],
            },
        ],
        expected=[
            {
                "_id": 1,
                "coverage_areas": [
                    {
                        "type": "Polygon",
                        "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                    },
                    {
                        "type": "Polygon",
                        "coordinates": [[[-50, -50], [50, -50], [50, 50], [-50, 50], [-50, -50]]],
                    },
                ],
            }
        ],
        msg="Array of Polygons should match if any element is entirely within",
    ),
    QueryTestCase(
        id="multiple_geospatial_fields",
        filter={"home": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "home": {"type": "Point", "coordinates": [0, 0]},
                "work": {"type": "Point", "coordinates": [50, 50]},
            },
            {
                "_id": 2,
                "home": {"type": "Point", "coordinates": [50, 50]},
                "work": {"type": "Point", "coordinates": [0, 0]},
            },
        ],
        expected=[
            {
                "_id": 1,
                "home": {"type": "Point", "coordinates": [0, 0]},
                "work": {"type": "Point", "coordinates": [50, 50]},
            }
        ],
        msg="Query on one geospatial field should not affect other fields",
    ),
    QueryTestCase(
        id="linestring_entirely_within",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {"_id": 1, "geo": {"type": "LineString", "coordinates": [[0, 0], [5, 5]]}},
            {"_id": 2, "geo": {"type": "LineString", "coordinates": [[0, 0], [50, 50]]}},
        ],
        expected=[{"_id": 1, "geo": {"type": "LineString", "coordinates": [[0, 0], [5, 5]]}}],
        msg="LineString entirely within should match",
    ),
    QueryTestCase(
        id="polygon_entirely_within",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                },
            },
            {
                "_id": 2,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[-50, -50], [50, -50], [50, 50], [-50, 50], [-50, -50]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                },
            }
        ],
        msg="Polygon entirely within should match",
    ),
    QueryTestCase(
        id="multipoint_all_within",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {"_id": 1, "geo": {"type": "MultiPoint", "coordinates": [[0, 0], [5, 5], [-5, -5]]}},
            {"_id": 2, "geo": {"type": "MultiPoint", "coordinates": [[0, 0], [50, 50]]}},
        ],
        expected=[
            {"_id": 1, "geo": {"type": "MultiPoint", "coordinates": [[0, 0], [5, 5], [-5, -5]]}}
        ],
        msg="MultiPoint should match only if all points are within",
    ),
    QueryTestCase(
        id="multilinestring_all_within",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 0], [5, 5]], [[-5, -5], [3, 3]]],
                },
            },
            {
                "_id": 2,
                "geo": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 0], [5, 5]], [[0, 0], [50, 50]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "geo": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 0], [5, 5]], [[-5, -5], [3, 3]]],
                },
            }
        ],
        msg="MultiLineString should match only if all lines are within",
    ),
    QueryTestCase(
        id="multilinestring_partial_no_match",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 0], [5, 5]], [[0, 0], [50, 50]]],
                },
            }
        ],
        expected=[],
        msg="MultiLineString with one line outside should not match",
    ),
    QueryTestCase(
        id="multipoint_partial_no_match",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {"_id": 1, "geo": {"type": "MultiPoint", "coordinates": [[0, 0], [50, 50]]}},
            {"_id": 2, "geo": {"type": "MultiPoint", "coordinates": [[1, 1], [2, 2]]}},
        ],
        expected=[{"_id": 2, "geo": {"type": "MultiPoint", "coordinates": [[1, 1], [2, 2]]}}],
        msg="MultiPoint with one point outside should not match",
    ),
    QueryTestCase(
        id="geometry_collection_all_within",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "LineString", "coordinates": [[1, 1], [2, 2]]},
                    ],
                },
            },
            {
                "_id": 2,
                "geo": {
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [50, 50]}],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "geo": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "LineString", "coordinates": [[1, 1], [2, 2]]},
                    ],
                },
            }
        ],
        msg="GeometryCollection with all sub-geometries within should match",
    ),
    QueryTestCase(
        id="geometry_collection_partial_no_match",
        filter={"geo": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "Point", "coordinates": [50, 50]},
                    ],
                },
            }
        ],
        expected=[],
        msg="GeometryCollection with one sub-geometry outside should not match",
    ),
]


ALL_TESTS = ARGUMENT_HANDLING_TESTS + NULL_MISSING_TESTS + DOCUMENT_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geoWithin_argument_handling(collection, test):
    """Test $geoWithin argument handling, data type coverage, and document types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
