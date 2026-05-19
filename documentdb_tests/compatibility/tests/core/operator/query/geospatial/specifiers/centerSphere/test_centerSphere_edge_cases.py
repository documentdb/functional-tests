"""Tests for $centerSphere edge cases — spherical geometry, radius boundaries,
antimeridian, poles."""

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
        id="spherical_vs_planar_divergence",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 60], 500 / 6371]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [7, 60]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 60]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [7, 60]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 60]}},
        ],
        msg="Should use spherical geometry (7 degrees longitude at lat 60 is ~390km)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_centerSphere_edge_cases(collection, test):
    """Verifies $centerSphere behavior at radius boundaries and spherical geometry edge cases."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
