"""
Tests for $geoIntersects core functionality — null/missing field handling,
field type validation, GeoJSON type intersection, valid geometry types,
degenerate geometry, legacy coordinate parsing, and basic intersection behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Standard query polygon
QUERY_POLYGON = {
    "$geometry": {
        "type": "Polygon",
        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
    }
}


NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_does_not_exist",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "other": "value"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Missing field should not match",
    ),
    QueryTestCase(
        id="field_is_null",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "loc": None},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Null field should not match",
    ),
]


FIELD_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_is_string",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "loc": "not geo"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="String field should not match",
    ),
    QueryTestCase(
        id="field_is_number",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[{"_id": 1, "loc": 42}, {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Numeric field should not match",
    ),
    QueryTestCase(
        id="field_is_boolean",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[{"_id": 1, "loc": True}, {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Boolean field should not match",
    ),
    QueryTestCase(
        id="field_is_array_of_geojson",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {
                "_id": 1,
                "loc": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [50, 50]},
                ],
            },
            {"_id": 2, "loc": [{"type": "Point", "coordinates": [50, 50]}]},
        ],
        expected=[
            {
                "_id": 1,
                "loc": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [50, 50]},
                ],
            }
        ],
        msg="Array of GeoJSON objects should match if any element intersects",
    ),
]


INTERSECTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="point_intersects_point_same_location",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Point query should intersect stored Point at same location",
    ),
    QueryTestCase(
        id="point_intersects_polygon_inside",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            }
        ],
        msg="Point query should intersect stored Polygon if point inside",
    ),
    QueryTestCase(
        id="linestring_intersects_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[0, 0], [20, 0]]}
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            }
        ],
        msg="LineString query should intersect stored Polygon if line crosses polygon",
    ),
    QueryTestCase(
        id="polygon_intersects_polygon_overlap",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-3, -3], [3, -3], [3, 3], [-3, 3], [-3, -3]]],
                    }
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            }
        ],
        msg="Polygon query should intersect stored Polygon if they overlap",
    ),
    QueryTestCase(
        id="polygon_intersects_point_inside",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Polygon query should intersect stored Point if point inside polygon",
    ),
    QueryTestCase(
        id="multipoint_intersects_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "MultiPoint", "coordinates": [[0, 0], [50, 50]]}
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            }
        ],
        msg="MultiPoint query should intersect if any point inside stored Polygon",
    ),
    QueryTestCase(
        id="polygon_no_intersection",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [60, 60]}},
        ],
        expected=[],
        msg="No documents should match when none intersect",
    ),
    QueryTestCase(
        id="geometrycollection_intersects",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "GeometryCollection",
                        "geometries": [
                            {"type": "Point", "coordinates": [0, 0]},
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="GeometryCollection query should intersect if any geometry in collection intersects",
    ),
    QueryTestCase(
        id="multipolygon_intersects_point",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                            [[[40, 40], [50, 40], [50, 50], [40, 50], [40, 40]]],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [45, 45]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [45, 45]}},
        ],
        msg="MultiPolygon should intersect if point in any polygon",
    ),
    QueryTestCase(
        id="linestring_crossing_linestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[-1, 1], [1, -1]]}
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "LineString", "coordinates": [[-1, -1], [1, 1]]}},
            {"_id": 2, "loc": {"type": "LineString", "coordinates": [[10, 10], [11, 11]]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "LineString", "coordinates": [[-1, -1], [1, 1]]}},
        ],
        msg="Crossing LineStrings should intersect",
    ),
    QueryTestCase(
        id="linestring_parallel_miss",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[0, 2], [1, 2]]}
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]}},
            {"_id": 2, "loc": {"type": "LineString", "coordinates": [[0, 5], [1, 5]]}},
        ],
        expected=[],
        msg="Parallel non-intersecting LineStrings should not match",
    ),
    QueryTestCase(
        id="linestring_vertex_touching",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[1, 0], [2, 1]]}
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]}},
            {"_id": 2, "loc": {"type": "LineString", "coordinates": [[5, 5], [6, 6]]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 0]]}},
        ],
        msg="LineStrings touching at vertex should intersect",
    ),
    QueryTestCase(
        id="linestring_point_intersection",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[-1, 0], [1, 0]]}
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="LineString should intersect Point on the line",
    ),
    QueryTestCase(
        id="tall_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-1, -60], [1, -60], [1, 60], [-1, 60], [-1, -60]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 45]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, -45]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 45]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, -45]}},
        ],
        msg="Tall polygon should intersect points within its latitude range",
    ),
    QueryTestCase(
        id="long_equatorial_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-60, -1], [60, -1], [60, 1], [-60, 1], [-60, -1]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [50, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-50, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 50]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [50, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-50, 0]}},
        ],
        msg="Long equatorial polygon should intersect points along equator",
    ),
]

STORED_MULTI_GEOMETRY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="stored_multipoint",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "loc": {"type": "MultiPoint", "coordinates": [[0, 0], [50, 50]]}},
            {"_id": 2, "loc": {"type": "MultiPoint", "coordinates": [[50, 50], [60, 60]]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "MultiPoint", "coordinates": [[0, 0], [50, 50]]}}],
        msg="Stored MultiPoint should match if any point intersects query polygon",
    ),
    QueryTestCase(
        id="stored_multilinestring",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiLineString",
                    "coordinates": [[[-1, 0], [1, 0]], [[50, 50], [51, 51]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "MultiLineString",
                    "coordinates": [[[50, 50], [51, 51]], [[60, 60], [61, 61]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiLineString",
                    "coordinates": [[[-1, 0], [1, 0]], [[50, 50], [51, 51]]],
                },
            }
        ],
        msg="Stored MultiLineString should match if any line intersects query polygon",
    ),
    QueryTestCase(
        id="stored_multipolygon",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                        [[[40, 40], [50, 40], [50, 50], [40, 50], [40, 40]]],
                    ],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[40, 40], [50, 40], [50, 50], [40, 50], [40, 40]]],
                        [[[60, 60], [70, 60], [70, 70], [60, 70], [60, 60]]],
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
                        [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                        [[[40, 40], [50, 40], [50, 50], [40, 50], [40, 40]]],
                    ],
                },
            }
        ],
        msg="Stored MultiPolygon should match if any polygon intersects query polygon",
    ),
    QueryTestCase(
        id="stored_geometrycollection",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "Point", "coordinates": [50, 50]},
                    ],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [50, 50]},
                    ],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "Point", "coordinates": [50, 50]},
                    ],
                },
            }
        ],
        msg="Stored GeometryCollection should match if any geometry intersects query polygon",
    ),
]

VALID_GEOMETRY_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="valid_point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects with Point geometry type should be valid",
    ),
    QueryTestCase(
        id="valid_linestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "LineString",
                        "coordinates": [[-1, 0], [1, 0]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects with LineString geometry type should be valid",
    ),
    QueryTestCase(
        id="valid_polygon",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects with Polygon geometry type should be valid",
    ),
    QueryTestCase(
        id="valid_multipoint",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiPoint",
                        "coordinates": [[0, 0], [50, 50]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects with MultiPoint geometry type should be valid",
    ),
    QueryTestCase(
        id="valid_multilinestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiLineString",
                        "coordinates": [[[-1, 0], [1, 0]], [[50, 50], [51, 51]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects with MultiLineString geometry type should be valid",
    ),
    QueryTestCase(
        id="valid_multipolygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                            [[[40, 40], [50, 40], [50, 50], [40, 50], [40, 40]]],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects with MultiPolygon geometry type should be valid",
    ),
    QueryTestCase(
        id="valid_geometrycollection",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "GeometryCollection",
                        "geometries": [
                            {"type": "Point", "coordinates": [0, 0]},
                            {
                                "type": "LineString",
                                "coordinates": [[50, 50], [51, 51]],
                            },
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects with GeometryCollection geometry type should be valid",
    ),
]

QUIRKY_BEHAVIOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="legacy_coordinates_array_match",
        filter={"loc": {"$geoIntersects": {"$geometry": [0, 0]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Legacy coordinate array matches point at same location",
    ),
    QueryTestCase(
        id="legacy_coordinates_array_no_match",
        filter={"loc": {"$geoIntersects": {"$geometry": [1, 2]}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[],
        msg="Legacy coordinate array does not match point at different location",
    ),
    QueryTestCase(
        id="legacy_doc_two_numeric_fields_match",
        filter={"loc": {"$geoIntersects": {"$geometry": {"x": 0, "y": 0}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Legacy doc form with 2 numeric fields matches point at same location",
    ),
    QueryTestCase(
        id="legacy_doc_arbitrary_field_names_match",
        filter={"loc": {"$geoIntersects": {"$geometry": {"a": 0, "b": 0}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Legacy doc form with arbitrary field names matches if values are numeric",
    ),
    QueryTestCase(
        id="coordinates_object_two_numeric_fields_matches",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": {"x": 0, "y": 0},
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Coordinates object with 2 numeric fields matches",
    ),
    QueryTestCase(
        id="coordinates_object_non_numeric_in_pos3_matches",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": {"x": 0, "y": 0, "z": "str"},
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Coordinates object with non-numeric in position 3 still matches",
    ),
    QueryTestCase(
        id="coordinates_object_three_numeric_fields_matches",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": {"a": 0, "b": 0, "c": 99},
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Coordinates object with 3 numeric fields still matches",
    ),
    QueryTestCase(
        id="coordinates_object_numeric_pos1_2_non_numeric_pos3_matches",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": {"a": 0, "b": 0, "c": "str"},
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Coordinates object with numeric in pos 1-2 and non-numeric in pos 3 still matches",
    ),
    QueryTestCase(
        id="extra_fields_in_geometry_ignored",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0], "extra": 1}
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Extra unrecognized fields in $geometry are silently ignored",
    ),
    QueryTestCase(
        id="zero_area_polygon_collinear_matches",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [2, 0], [0, 0]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Zero-area polygon with collinear points does not error and can match",
    ),
    QueryTestCase(
        id="stored_invalid_geojson_skipped",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Polygon", "coordinates": []}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Stored invalid GeoJSON is silently skipped without index",
    ),
]

DEGENERATE_GEOMETRY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="polygon_vertex_sharing_no_intersect",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[10, 10], [20, 10], [20, 20], [10, 20], [10, 10]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                },
            }
        ],
        msg="Polygons sharing only a vertex do not intersect",
    ),
    QueryTestCase(
        id="polygon_edge_sharing_no_intersect",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                },
            },
            {
                "_id": 2,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[10, 0], [20, 0], [20, 10], [10, 10], [10, 0]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                },
            }
        ],
        msg="Polygons sharing only an edge do not intersect",
    ),
    QueryTestCase(
        id="stored_polygon_with_hole_point_inside_hole",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [
                        [[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]],
                        [[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]],
                    ],
                },
            },
        ],
        expected=[],
        msg="Point inside hole of stored polygon should not intersect",
    ),
    QueryTestCase(
        id="stored_polygon_with_hole_point_in_ring",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [7, 7]}}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [
                        [[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]],
                        [[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]],
                    ],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [
                        [[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]],
                        [[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]],
                    ],
                },
            },
        ],
        msg="Point in ring area of stored polygon with hole should intersect",
    ),
    QueryTestCase(
        id="dot_notation_nested_geojson",
        filter={
            "geo.loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "geo": {"loc": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "geo": {"loc": {"type": "Point", "coordinates": [50, 50]}}},
        ],
        expected=[{"_id": 1, "geo": {"loc": {"type": "Point", "coordinates": [0, 0]}}}],
        msg="$geoIntersects should work with dot notation on nested field",
    ),
]

ALL_TESTS = (
    NULL_MISSING_TESTS
    + FIELD_TYPE_TESTS
    + INTERSECTION_TESTS
    + STORED_MULTI_GEOMETRY_TESTS
    + VALID_GEOMETRY_TYPE_TESTS
    + QUIRKY_BEHAVIOR_TESTS
    + DEGENERATE_GEOMETRY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geoIntersects_core(collection, test):
    """Test $geoIntersects core functionality and valid geometry types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
