"""Tests for $geometry polygon edge cases — odd shapes, degenerate geometry,
and polygon holes."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ODD_SHAPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="many_vertices_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[i * 0.36 - 180, -0.5 if i % 2 == 0 else 0.5] for i in range(1000)]
                            + [[-180, -0.5]]
                        ],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept polygon with 1000+ vertices",
    ),
    QueryTestCase(
        id="collinear_points_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [2, 0], [2, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0.5]}}],
        msg="Should accept polygon with collinear points on edge",
    ),
    QueryTestCase(
        id="duplicate_consecutive_vertices",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should accept polygon with duplicate consecutive vertices",
    ),
    QueryTestCase(
        id="degenerate_same_location_points",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "MultiPoint", "coordinates": [[0, 0], [0, 0], [0, 0]]}
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should handle degenerate geometry (all points same location)",
    ),
]


POLYGON_HOLE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="polygon_with_hole",
        filter={
            "loc": {
                "$geoIntersects": {
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


ALL_TESTS = ODD_SHAPE_TESTS + POLYGON_HOLE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geometry_polygon_edge_cases(collection, test):
    """Verifies $geometry handles polygon edge cases correctly."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
