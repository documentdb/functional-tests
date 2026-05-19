"""
Tests for $polygon edge cases.

Validates degenerate polygons, boundary coordinates, boundary inclusion
(points on edges and vertices), self-intersecting polygons, duplicate
points, and large point counts.
"""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# 100-point polygon approximating a circle of radius 50 centered at (50, 50)
_CIRCLE_POINTS = [
    [50 + 50 * math.cos(2 * math.pi * i / 100), 50 + 50 * math.sin(2 * math.pi * i / 100)]
    for i in range(100)
]

DEGENERATE_POLYGON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="all_points_identical",
        filter={"loc": {"$geoWithin": {"$polygon": [[1, 1], [1, 1], [1, 1]]}}},
        doc=[{"_id": 1, "loc": [1, 1]}, {"_id": 2, "loc": [2, 2]}],
        expected=[{"_id": 1, "loc": [1, 1]}],
        msg="Degenerate polygon with all identical points should match point at that location",
    ),
    QueryTestCase(
        id="collinear_points_x_axis",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [5, 0], [10, 0]]}}},
        doc=[{"_id": 1, "loc": [3, 0]}, {"_id": 2, "loc": [3, 5]}],
        expected=[{"_id": 1, "loc": [3, 0]}],
        msg="Collinear points along x-axis should match points on the line segment",
    ),
    QueryTestCase(
        id="collinear_points_y_axis",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 5], [0, 10]]}}},
        doc=[{"_id": 1, "loc": [0, 3]}, {"_id": 2, "loc": [5, 3]}],
        expected=[{"_id": 1, "loc": [0, 3]}],
        msg="Collinear points along y-axis should match points on the line segment",
    ),
    QueryTestCase(
        id="two_distinct_one_duplicate",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [5, 5], [0, 0]]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [5, 5]}, {"_id": 3, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [5, 5]}],
        msg="Degenerate polygon with duplicate should match points on segment",
    ),
    QueryTestCase(
        id="consecutive_duplicate_points",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 0], [5, 5], [10, 0]]}}},
        doc=[{"_id": 1, "loc": [4, 2]}, {"_id": 2, "loc": [20, 20]}],
        expected=[{"_id": 1, "loc": [4, 2]}],
        msg="Polygon with consecutive duplicate points should still work",
    ),
    QueryTestCase(
        id="self_intersecting_bowtie",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 10], [10, 0], [0, 10]]}}},
        doc=[
            {"_id": 1, "loc": [2, 2]},
            {"_id": 2, "loc": [8, 8]},
            {"_id": 3, "loc": [5, 5]},
        ],
        expected=[{"_id": 1, "loc": [2, 2]}, {"_id": 3, "loc": [5, 5]}],
        msg="Self-intersecting bowtie should match points in its triangles",
    ),
]


BOUNDARY_COORDINATE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="coordinates_at_zero",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [1, 0], [0, 1]]}}},
        doc=[{"_id": 1, "loc": [0.2, 0.2]}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 1, "loc": [0.2, 0.2]}],
        msg="Polygon at origin should work",
    ),
    QueryTestCase(
        id="small_fractional_coordinates",
        filter={
            "loc": {
                "$geoWithin": {
                    "$polygon": [[0.0001, 0.0001], [0.0001, 0.001], [0.001, 0.001], [0.001, 0.0001]]
                }
            }
        },
        doc=[{"_id": 1, "loc": [0.0005, 0.0005]}, {"_id": 2, "loc": [1, 1]}],
        expected=[{"_id": 1, "loc": [0.0005, 0.0005]}],
        msg="Polygon with very small fractional coordinates should work",
    ),
    QueryTestCase(
        id="longitude_latitude_bounds",
        filter={
            "loc": {"$geoWithin": {"$polygon": [[-180, -90], [180, -90], [180, 90], [-180, 90]]}}
        },
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [45, 45]}],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [45, 45]}],
        msg="Polygon at lon/lat bounds should contain all points within",
    ),
    QueryTestCase(
        id="negative_zero_coordinate",
        filter={
            "loc": {"$geoWithin": {"$polygon": [[-0.0, -0.0], [-0.0, 10], [10, 10], [10, -0.0]]}}
        },
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Negative zero should behave same as zero",
    ),
]


BOUNDARY_INCLUSION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="point_on_polygon_edge",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [5, 0]},  # midpoint of bottom edge
            {"_id": 2, "loc": [5, 5]},  # inside
            {"_id": 3, "loc": [15, 15]},  # outside
        ],
        expected=[{"_id": 1, "loc": [5, 0]}, {"_id": 2, "loc": [5, 5]}],
        msg="Point on polygon edge should match",
    ),
    QueryTestCase(
        id="point_on_polygon_vertex",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [0, 0]},  # on vertex
            {"_id": 2, "loc": [5, 5]},  # inside
            {"_id": 3, "loc": [15, 15]},  # outside
        ],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [5, 5]}],
        msg="Point on polygon vertex should match",
    ),
    QueryTestCase(
        id="point_on_diagonal_edge",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [5, 5]},  # midpoint of hypotenuse [0,0]->[10,10]
            {"_id": 2, "loc": [3, 3]},  # on hypotenuse
            {"_id": 3, "loc": [5, 1]},  # inside triangle
            {"_id": 4, "loc": [0, 10]},  # outside
        ],
        expected=[{"_id": 3, "loc": [5, 1]}],
        msg="Point on non-axis-aligned (diagonal) edge is not included",
    ),
    QueryTestCase(
        id="point_collinear_beyond_segment",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [15, 15]},  # collinear with [0,0]->[10,10] but beyond
            {"_id": 2, "loc": [-5, -5]},  # collinear but before start
            {"_id": 3, "loc": [5, 1]},  # inside triangle
        ],
        expected=[{"_id": 3, "loc": [5, 1]}],
        msg="Point collinear with edge but beyond segment should not match",
    ),
]

LARGE_POINT_COUNT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="large_point_count",
        filter={"loc": {"$geoWithin": {"$polygon": _CIRCLE_POINTS}}},
        doc=[
            {"_id": 1, "loc": [50, 50]},  # center - inside
            {"_id": 2, "loc": [50, 75]},  # inside
            {"_id": 3, "loc": [50, 110]},  # outside
        ],
        expected=[{"_id": 1, "loc": [50, 50]}, {"_id": 2, "loc": [50, 75]}],
        msg="Many-point polygon should work",
    ),
]


EDGE_CASE_TESTS: list[QueryTestCase] = (
    DEGENERATE_POLYGON_TESTS
    + BOUNDARY_COORDINATE_TESTS
    + BOUNDARY_INCLUSION_TESTS
    + LARGE_POINT_COUNT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_polygon_edge_cases(collection, test):
    """Test $polygon edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
