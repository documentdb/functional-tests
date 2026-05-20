"""Tests for $geometry polygon edge cases — odd shapes, winding order, degenerate polygons."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Odd polygon shapes (from geo_s2oddshapes.js) ---

ODD_SHAPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="tall_narrow_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-0.5, -89], [0.5, -89], [0.5, 89], [-0.5, 89], [-0.5, -89]]
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should find point inside tall narrow polygon (1 degree wide, 178 degrees tall)",
    ),
    QueryTestCase(
        id="very_small_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0.001, 0], [0.001, 0.001], [0, 0.001], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.0005, 0.0005]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.0005, 0.0005]}}],
        msg="Should find point inside very small polygon",
    ),
]


# --- Polygon with hole ---

POLYGON_HOLE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="polygon_with_hole",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]],
                            [
                                [0.1, 0.1],
                                [0.1, 0.9],
                                [0.9, 0.9],
                                [0.9, 0.1],
                                [0.1, 0.1],
                            ],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [3, 3]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [3, 3]}}],
        msg="Should exclude points inside the hole",
    ),
]


# --- Winding order ---

WINDING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="ccw_winding_matches_interior",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should match interior of counter-clockwise polygon",
    ),
]


ALL_TESTS = ODD_SHAPE_TESTS + POLYGON_HOLE_TESTS + WINDING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geometry_polygon_edge_cases(collection, test):
    """Verifies $geometry handles polygon edge cases correctly."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
