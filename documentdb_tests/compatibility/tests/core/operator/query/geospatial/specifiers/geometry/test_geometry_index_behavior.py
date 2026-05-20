"""Tests for $geometry index behavior — 2dsphere index requirements."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import NO_QUERY_EXECUTION_PLANS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UNIT_POLYGON = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]

# --- Error: $near requires a 2dsphere index ---

INDEX_REQUIRED_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_without_index_errors",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should error when $near used without geospatial index",
    ),
]

# --- Success: operators that work without a 2dsphere index ---

NO_INDEX_SUCCESS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geoWithin_without_index_works",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": UNIT_POLYGON,
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should work without index for $geoWithin (collection scan)",
    ),
    QueryTestCase(
        id="geoIntersects_without_index_works",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": UNIT_POLYGON,
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should work without index for $geoIntersects (collection scan)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INDEX_REQUIRED_TESTS))
def test_geometry_index_required_errors(collection, test):
    """Verifies $near with $geometry errors without a 2dsphere index."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NO_INDEX_SUCCESS_TESTS))
def test_geometry_no_index_success(collection, test):
    """Verifies $geoWithin/$geoIntersects work without a 2dsphere index."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
