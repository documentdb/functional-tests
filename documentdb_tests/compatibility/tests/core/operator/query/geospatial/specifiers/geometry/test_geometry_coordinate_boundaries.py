"""Tests for $geometry valid coordinate boundary values — longitude/latitude limits."""

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
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        msg="Should accept longitude = -180",
    ),
    QueryTestCase(
        id="longitude_positive_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [180, 0]}}}
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        msg="Should accept longitude = 180",
    ),
    QueryTestCase(
        id="latitude_negative_90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, -90]}}}
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        msg="Should accept latitude = -90",
    ),
    QueryTestCase(
        id="latitude_positive_90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 90]}}}
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        msg="Should accept latitude = 90",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_BOUNDARY_TESTS))
def test_geometry_coordinate_boundaries(collection, test):
    """Verifies $geometry accepts coordinates at valid boundary values."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
