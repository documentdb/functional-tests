"""Tests for $centerSphere edge cases — radius boundaries, antimeridian,
poles, nested fields, coordinate order, unit conversion, boundary
precision, array of points, and spherical vs planar comparison."""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_INFINITY

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="radius_zero",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.001, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should match only exact center point with radius=0",
    ),
    QueryTestCase(
        id="very_small_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1e-10]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.001, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should work with very small radius",
    ),
    QueryTestCase(
        id="radius_pi_half_hemisphere",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], math.pi / 2]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [89, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 89]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [89, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 89]}},
        ],
        msg="Should cover hemisphere with radius = pi/2",
    ),
    QueryTestCase(
        id="infinity_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], FLOAT_INFINITY]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should return all documents with Infinity radius",
    ),
    QueryTestCase(
        id="antimeridian_crossing",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[180, 0], 5 / 6371]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179.99, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179.99, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179.99, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179.99, 0]}},
        ],
        msg="Should find points across antimeridian",
    ),
    QueryTestCase(
        id="pole_proximity_north",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 90], 200 / 6371]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [90, 89]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [180, 89]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [90, 89]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [180, 89]}},
        ],
        msg="Should find points near North Pole regardless of longitude",
    ),
    QueryTestCase(
        id="nested_field_path",
        filter={"address.location": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
        doc=[
            {"_id": 1, "address": {"location": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "address": {"location": {"type": "Point", "coordinates": [50, 50]}}},
        ],
        expected=[
            {"_id": 1, "address": {"location": {"type": "Point", "coordinates": [0, 0]}}},
        ],
        msg="Should work with nested field path",
    ),
    QueryTestCase(
        id="coordinate_order_sensitivity",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[-74, 40], 0.001]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-74, 40]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [40, -74]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-74, 40]}}],
        msg="Should use [lng, lat] order — swapped coordinates should not match",
    ),
    QueryTestCase(
        id="radius_conversion_miles",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[-88, 30], 10 / 3963.2]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-88, 30]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-88.1, 30]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, 30]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-88, 30]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-88.1, 30]}},
        ],
        msg="Should correctly convert miles to radians (10 miles / 3963.2)",
    ),
    QueryTestCase(
        id="point_exactly_on_sphere_boundary",
        filter={
            "loc": {
                "$geoWithin": {
                    # 1 degree along equator = pi/180 radians
                    "$centerSphere": [[0, 0], math.radians(1)]
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.5, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.5, 0]}},
        ],
        msg="Point exactly at radius distance should be included",
    ),
    QueryTestCase(
        id="point_just_beyond_sphere_boundary",
        filter={
            "loc": {
                "$geoWithin": {
                    # 100km radius in radians
                    "$centerSphere": [[0, 0], 100 / 6371]
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.5, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.5, 0]}},
        ],
        msg="Point beyond sphere boundary should not be included",
    ),
    QueryTestCase(
        id="point_on_boundary_non_cardinal_angle",
        filter={
            "loc": {
                "$geoWithin": {
                    # 1 degree in radians — should reach a point ~1 degree away
                    # at a 45-degree bearing
                    "$centerSphere": [[0, 0], math.radians(1)]
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0.9, 0.9]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Point at non-cardinal angle near boundary should respect spherical distance",
    ),
    QueryTestCase(
        id="radius_slightly_above_pi",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], math.pi + 0.1]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, -45]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, -45]}},
        ],
        msg="Radius slightly above pi should still return all documents",
    ),
    QueryTestCase(
        id="array_of_points_field",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
        doc=[
            {
                "_id": 1,
                "loc": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [50, 50]},
                ],
            },
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[
            {
                "_id": 1,
                "loc": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [50, 50]},
                ],
            },
        ],
        msg="Should match document when any element in array of points is within sphere",
    ),
    QueryTestCase(
        id="center_vs_centerSphere_comparison",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 60], 500 / 6371]}}},
        doc=[
            {"_id": 1, "loc": [0, 60]},
            {"_id": 2, "loc": [8, 60]},
            {"_id": 3, "loc": [0, 55]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 60]},
            {"_id": 2, "loc": [8, 60]},
        ],
        msg=(
            "$centerSphere uses spherical distance — 8 degrees longitude "
            "at lat 60 is ~446km (within 500km), unlike planar $center"
        ),
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_centerSphere_edge_cases(collection, test):
    """Verifies $centerSphere behavior at radius boundaries and spherical geometry edge cases."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
