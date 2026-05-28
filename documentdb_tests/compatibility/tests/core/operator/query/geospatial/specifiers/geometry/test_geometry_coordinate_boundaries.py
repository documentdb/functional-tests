"""Tests for $geometry valid coordinate boundary values — longitude/latitude limits,
poles, longitude non-equivalence at antimeridian, pole longitude equivalence,
origin, negative coordinates, and high-precision coordinates."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

VALID_BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_negative_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [-180, 0]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        msg="Should accept longitude = -180",
    ),
    QueryTestCase(
        id="longitude_positive_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [180, 0]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        msg="Should accept longitude = 180",
    ),
    QueryTestCase(
        id="latitude_negative_90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, -90]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        msg="Should accept latitude = -90",
    ),
    QueryTestCase(
        id="origin_zero_zero",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [45, 45]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept coordinates at origin (0, 0)",
    ),
    QueryTestCase(
        id="negative_coordinates",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [-45, -45]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-45, -45]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [45, 45]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-45, -45]}}],
        msg="Should accept negative longitude and latitude",
    ),
    QueryTestCase(
        id="lng_180_does_not_match_negative_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [180, 0]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        msg="Longitude 180 and -180 should not be treated as equivalent (strict numeric)",
    ),
    QueryTestCase(
        id="north_pole_any_longitude",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 90]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 90]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, 90]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 90]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-90, 90]}},
        ],
        msg="At the North Pole (lat=90), longitude is irrelevant — all pole points should match",
    ),
    QueryTestCase(
        id="high_precision_coordinates",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [1.123456789012345, 2.123456789012345],
                    }
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1.123456789012345, 2.123456789012345]},
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1.123456789012345, 2.123456789012345]},
            },
        ],
        msg="Should accept high-precision coordinates (15+ decimal places)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_BOUNDARY_TESTS))
def test_geometry_coordinate_boundaries(collection, test):
    """Verifies $geometry accepts coordinates at valid boundary values."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
