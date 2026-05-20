"""Tests for $geometry valid CRS (strictwinding) usage."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

STRICT_CRS = {
    "type": "name",
    "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
}

CCW_POLYGON = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]


# --- Valid CRS usage ---

VALID_CRS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="crs_with_geoWithin",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": CCW_POLYGON,
                        "crs": STRICT_CRS,
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should accept custom CRS with $geoWithin",
    ),
    QueryTestCase(
        id="crs_with_geoIntersects",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": CCW_POLYGON,
                        "crs": STRICT_CRS,
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should accept custom CRS with $geoIntersects",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_CRS_TESTS))
def test_geometry_crs(collection, test):
    """Verifies $geometry accepts valid custom CRS with supported operators."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
