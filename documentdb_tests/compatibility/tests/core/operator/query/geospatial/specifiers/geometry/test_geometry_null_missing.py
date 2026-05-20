"""Tests for $geometry null/missing field handling."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POLYGON_FILTER = {
    "loc": {
        "$geoWithin": {
            "$geometry": {
                "type": "Polygon",
                "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
            }
        }
    }
}

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_location_not_matched",
        filter=POLYGON_FILTER,
        doc=[
            {"_id": 1, "loc": None},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should not match documents where location field is null",
    ),
    QueryTestCase(
        id="missing_location_not_matched",
        filter=POLYGON_FILTER,
        doc=[
            {"_id": 1, "name": "no_loc"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should not match documents where location field is missing",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_MISSING_TESTS))
def test_geometry_null_missing(collection, test):
    """Verifies $geometry queries skip documents with null or missing location fields."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
