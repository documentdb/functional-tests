"""
Tests for $geoWithin legacy shape operators ($box, $polygon, $center, $centerSphere).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

LEGACY_SHAPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="box_points_inside",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$box should match points inside",
    ),
    QueryTestCase(
        id="polygon_points_inside",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$polygon should match points inside",
    ),
    QueryTestCase(
        id="center_points_within_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[{"_id": 1, "loc": [1, 1]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [1, 1]}],
        msg="$center should match points within flat circle radius",
    ),
    QueryTestCase(
        id="centersphere_points_within",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
        doc=[{"_id": 1, "loc": [0.1, 0.1]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [0.1, 0.1]}],
        msg="$centerSphere should match points within spherical circle",
    ),
]


# Flat operators ($box, $polygon, $center) accept legacy [x, y] pairs and
# GeoJSON Point documents (the Point's coordinates are used). Non-Point
# GeoJSON document types (LineString, Polygon, etc.) silently do not match.
FLAT_OPERATOR_GEOJSON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="box_with_geojson_point_matches",
        filter={"loc": {"$geoWithin": {"$box": [[-10, -10], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$box should match GeoJSON Point inside the box",
    ),
    QueryTestCase(
        id="box_with_geojson_linestring_no_match",
        filter={"loc": {"$geoWithin": {"$box": [[-10, -10], [10, 10]]}}},
        doc=[{"_id": 1, "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}}],
        expected=[],
        msg="$box should silently not match non-Point GeoJSON document",
    ),
    QueryTestCase(
        id="polygon_with_geojson_point_matches",
        filter={"loc": {"$geoWithin": {"$polygon": [[-10, -10], [10, -10], [10, 10], [-10, 10]]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$polygon should match GeoJSON Point inside the polygon",
    ),
    QueryTestCase(
        id="center_with_geojson_point_matches",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$center should match GeoJSON Point inside the radius",
    ),
]


ALL_TESTS = LEGACY_SHAPE_TESTS + FLAT_OPERATOR_GEOJSON_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geoWithin_legacy_shapes(collection, test):
    """Test $geoWithin legacy shape operators ($box, $polygon, $center, $centerSphere)."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
