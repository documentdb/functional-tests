"""Tests for $nearSphere edge cases — distance calculation, duplicate coordinates."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

GEOJSON_DISTANCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="spherical_distance_50km_excludes_1_degree",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": 50000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should use spherical distance (meters) — 50km excludes point at 1 degree",
    ),
    QueryTestCase(
        id="spherical_distance_120km_includes_1_degree",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": 120000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        msg="Should include point within 120km",
    ),
    QueryTestCase(
        id="antipodal_points",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": 20100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
        ],
        msg="Should find antipodal point with maxDistance > half Earth circumference",
    ),
    QueryTestCase(
        id="duplicate_coordinates",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        msg="Should return all documents at same coordinates without deduplication",
    ),
]


ALL_DISTANCE_TESTS: list[QueryTestCase] = GEOJSON_DISTANCE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_DISTANCE_TESTS))
def test_nearSphere_distance(collection, test):
    """Verifies $nearSphere distance calculations."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
