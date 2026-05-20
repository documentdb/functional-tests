"""Tests for $geometry valid argument handling —
valid structures, field ordering, and CRS."""

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

# --- Success cases: valid $geometry structures ---

VALID_GEOMETRY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="valid_point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept valid Point $geometry",
    ),
    QueryTestCase(
        id="extra_field_in_geometry",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0], "extra": 1}
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should ignore extra fields in $geometry",
    ),
    QueryTestCase(
        id="coordinates_before_type",
        filter={"loc": {"$geoIntersects": {"$geometry": {"coordinates": [0, 0], "type": "Point"}}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept coordinates before type (field order doesn't matter)",
    ),
    QueryTestCase(
        id="crs_with_geoWithin",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
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
        id="array_value_no_error",
        filter={"loc": {"$geoIntersects": {"$geometry": [0, 0]}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geometry: array value does not error, geometry specifier is silently ignored",
    ),
    QueryTestCase(
        id="crs_with_geoIntersects",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
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


@pytest.mark.parametrize("test", pytest_params(VALID_GEOMETRY_TESTS))
def test_geometry_argument_handling(collection, test):
    """Verifies $geometry accepts valid GeoJSON structures."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
