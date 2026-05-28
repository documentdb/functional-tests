"""Tests for $near edge cases — coordinate boundaries, extreme coordinates."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.usefixtures("geo_2dsphere")


COORDINATE_BOUNDARY_SUCCESS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_neg180",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [-180, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        msg="Should accept longitude = -180",
    ),
    QueryTestCase(
        id="longitude_180",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [180, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        msg="Should accept longitude = 180",
    ),
    QueryTestCase(
        id="latitude_neg90",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, -90]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        msg="Should accept latitude = -90",
    ),
    QueryTestCase(
        id="latitude_90",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 90]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        msg="Should accept latitude = 90",
    ),
    QueryTestCase(
        id="negative_zero_coordinate",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [-0.0, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept negative zero coordinate",
    ),
]

EXTREME_COORDINATE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="north_pole",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 90]},
                    "$maxDistance": 20100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should query from North Pole",
    ),
    QueryTestCase(
        id="south_pole",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, -90]},
                    "$maxDistance": 20100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should query from South Pole",
    ),
    QueryTestCase(
        id="antimeridian_180",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [180, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-180, 0]}},
        ],
        msg="Should find points at antimeridian (180 and -180 are same location)",
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(COORDINATE_BOUNDARY_SUCCESS_TESTS + EXTREME_COORDINATE_TESTS)
)
def test_near_edge_cases(collection, test):
    """Verifies $near handles boundary and extreme coordinate cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
