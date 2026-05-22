"""Tests for $geometry index behavior — without index, with 2d index,
and with compound 2dsphere index."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UNIT_POLYGON = [[[-1, -1], [5, -1], [5, 5], [-1, 5], [-1, -1]]]

NO_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geoWithin_without_index",
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
        msg="$geometry should work without index for $geoWithin (collection scan)",
    ),
    QueryTestCase(
        id="geoIntersects_without_index",
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
        msg="$geometry should work without index for $geoIntersects (collection scan)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NO_INDEX_TESTS))
def test_geometry_no_index(collection, test):
    """Verifies $geometry works without any geospatial index."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


WITH_2D_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geoWithin_with_2d_index",
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
            {"_id": 1, "loc": [0.5, 0.5]},
            {"_id": 2, "loc": [10, 10]},
        ],
        expected=[{"_id": 1, "loc": [0.5, 0.5]}],
        msg="$geometry should work with 2d index for $geoWithin",
    ),
    QueryTestCase(
        id="geoIntersects_with_2d_index",
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
            {"_id": 1, "loc": [0.5, 0.5]},
            {"_id": 2, "loc": [10, 10]},
        ],
        expected=[{"_id": 1, "loc": [0.5, 0.5]}],
        msg="$geometry should work with 2d index for $geoIntersects",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WITH_2D_INDEX_TESTS))
def test_geometry_with_2d_index(collection, test):
    """Verifies $geometry works with a 2d index (alternate index type)."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


COMPOUND_2DSPHERE_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geoWithin_compound_2dsphere",
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
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "a"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}, "type": "b"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "a"},
        ],
        msg="$geometry should work with compound 2dsphere index for $geoWithin",
    ),
    QueryTestCase(
        id="geoIntersects_compound_2dsphere",
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
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "a"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}, "type": "b"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "a"},
        ],
        msg="$geometry should work with compound 2dsphere index for $geoIntersects",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMPOUND_2DSPHERE_INDEX_TESTS))
def test_geometry_compound_2dsphere_index(collection, test):
    """Verifies $geometry works with a compound 2dsphere + ascending index."""
    collection.create_index([("loc", "2dsphere"), ("type", 1)])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
