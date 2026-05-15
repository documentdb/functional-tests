"""
Tests for $polygon core geometric behavior.

Validates valid point counts, point containment, concave polygon shapes,
winding order invariance, implicit and explicit closure, coordinate
behavior, and planar geometry.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

VALID_POINT_COUNT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="three_points_triangle",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [3, 6], [6, 0]]}}},
        doc=[{"_id": 1, "loc": [2, 2]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [2, 2]}],
        msg="$polygon with 3 points (triangle) should succeed",
    ),
    QueryTestCase(
        id="four_points_quadrilateral",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 5], [5, 5], [5, 0]]}}},
        doc=[{"_id": 1, "loc": [2, 2]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [2, 2]}],
        msg="$polygon with 4 points (quadrilateral) should succeed",
    ),
    QueryTestCase(
        id="five_points_pentagon",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [2, 5], [5, 5], [7, 2], [4, -1]]}}},
        doc=[{"_id": 1, "loc": [3, 3]}, {"_id": 2, "loc": [20, 20]}],
        expected=[{"_id": 1, "loc": [3, 3]}],
        msg="$polygon with 5 points (pentagon) should succeed",
    ),
]

POINT_CONTAINMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="point_inside_triangle",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [5, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 3]}, {"_id": 2, "loc": [20, 20]}],
        expected=[{"_id": 1, "loc": [5, 3]}],
        msg="Point inside triangle should match",
    ),
    QueryTestCase(
        id="point_outside_triangle",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [5, 10]]}}},
        doc=[{"_id": 1, "loc": [20, 20]}, {"_id": 2, "loc": [-5, -5]}],
        expected=[],
        msg="Points outside triangle should not match",
    ),
    QueryTestCase(
        id="point_at_origin_inside",
        filter={"loc": {"$geoWithin": {"$polygon": [[-5, -5], [5, -5], [5, 5], [-5, 5]]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Point at origin inside polygon should match",
    ),
    QueryTestCase(
        id="multiple_points_inside_and_outside",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [2, 8]},
            {"_id": 3, "loc": [15, 15]},
            {"_id": 4, "loc": [-1, -1]},
        ],
        expected=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [2, 8]}],
        msg="Only points inside polygon should match",
    ),
    QueryTestCase(
        id="concave_excludes_concavity",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [5, 7], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [2, 2]},
            {"_id": 2, "loc": [8, 2]},
            {"_id": 3, "loc": [5, 9]},
        ],
        expected=[{"_id": 1, "loc": [2, 2]}, {"_id": 2, "loc": [8, 2]}],
        msg="Concave polygon should correctly exclude points in concavity",
    ),
]

WINDING_ORDER_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="counter_clockwise_winding",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="CCW winding should produce same results as CW",
    ),
]

CLOSURE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="implicit_closure",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [5, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Implicitly closed polygon should contain point",
    ),
    QueryTestCase(
        id="explicit_closure",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [5, 10], [0, 0]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Explicitly closed polygon should produce same results as implicit",
    ),
]

COORDINATE_BEHAVIOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negative_coordinates",
        filter={"loc": {"$geoWithin": {"$polygon": [[-5, -5], [-5, 5], [5, 5], [5, -5]]}}},
        doc=[{"_id": 1, "loc": [-2, -2]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [-2, -2]}],
        msg="Polygon with negative coordinates should work",
    ),
    QueryTestCase(
        id="large_coordinates",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 1000], [1000, 1000], [1000, 0]]}}},
        doc=[{"_id": 1, "loc": [500, 500]}, {"_id": 2, "loc": [2000, 2000]}],
        expected=[{"_id": 1, "loc": [500, 500]}],
        msg="Polygon with large coordinates should work",
    ),
    QueryTestCase(
        id="longitude_first_convention",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [10, 2], [0, 2]]}}},
        doc=[{"_id": 1, "loc": [5, 1]}, {"_id": 2, "loc": [1, 5]}],
        expected=[{"_id": 1, "loc": [5, 1]}],
        msg="$polygon should use longitude-first convention",
    ),
    QueryTestCase(
        id="no_holes_support",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$polygon accepts only exterior ring, no holes syntax",
    ),
]

PLANAR_GEOMETRY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="antimeridian_no_wrap",
        filter={"loc": {"$geoWithin": {"$polygon": [[-179, -1], [179, -1], [179, 1], [-179, 1]]}}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [179, 0]},
            {"_id": 3, "loc": [-179, 0]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [179, 0]},
            {"_id": 3, "loc": [-179, 0]},
        ],
        msg="Planar geometry should not wrap at antimeridian",
    ),
    QueryTestCase(
        id="planar_large_area",
        filter={
            "loc": {"$geoWithin": {"$polygon": [[-100, -90], [100, -90], [100, 90], [-100, 90]]}}
        },
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
            {"_id": 3, "loc": [100, 80]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
            {"_id": 3, "loc": [100, 80]},
        ],
        msg="Large polygon should use flat geometry",
    ),
]

CORE_FUNCTIONALITY_TESTS: list[QueryTestCase] = (
    VALID_POINT_COUNT_TESTS
    + POINT_CONTAINMENT_TESTS
    + WINDING_ORDER_TESTS
    + CLOSURE_TESTS
    + COORDINATE_BEHAVIOR_TESTS
    + PLANAR_GEOMETRY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CORE_FUNCTIONALITY_TESTS))
def test_polygon_core(collection, test):
    """Test $polygon core geometric behavior."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
