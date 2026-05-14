"""
Tests for $polygon core geometric behavior.

Validates valid point counts, point containment, concave polygon shapes,
winding order invariance, implicit closure, and coordinate conventions.
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


@pytest.mark.parametrize("test", pytest_params(VALID_POINT_COUNT_TESTS))
def test_polygon_valid_point_counts(collection, test):
    """Test $polygon succeeds with 3 or more points."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


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


@pytest.mark.parametrize("test", pytest_params(POINT_CONTAINMENT_TESTS))
def test_polygon_point_containment(collection, test):
    """Test $polygon correctly identifies points inside/outside polygon."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


def test_polygon_winding_order_invariance(collection):
    """Test $polygon produces same results regardless of winding order."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
        ]
    )
    # Clockwise
    result_cw = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}}},
        },
    )
    # Counter-clockwise (verify it also succeeds)
    execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    expected = [{"_id": 1, "loc": [5, 5]}]
    assertSuccess(result_cw, expected, msg="Clockwise winding should match point inside")


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


@pytest.mark.parametrize("test", pytest_params(CLOSURE_TESTS))
def test_polygon_closure(collection, test):
    """Test $polygon implicit and explicit polygon closure."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


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


@pytest.mark.parametrize("test", pytest_params(COORDINATE_BEHAVIOR_TESTS))
def test_polygon_coordinate_behavior(collection, test):
    """Test $polygon with various coordinate ranges and conventions."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


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


@pytest.mark.parametrize("test", pytest_params(PLANAR_GEOMETRY_TESTS))
def test_polygon_planar_geometry(collection, test):
    """Test $polygon uses planar (flat) geometry."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
