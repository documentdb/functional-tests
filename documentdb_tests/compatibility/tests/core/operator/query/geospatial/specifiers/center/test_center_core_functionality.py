"""Tests for $center core functionality."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="returns_documents_within_circle",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 2]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 1]}, {"_id": 3, "loc": [5, 5]}],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 1]}],
        msg="Should return documents within circular bounds",
    ),
    QueryTestCase(
        id="point_at_center_matches",
        filter={"loc": {"$geoWithin": {"$center": [[10, 10], 5]}}},
        doc=[{"_id": 1, "loc": [10, 10]}, {"_id": 2, "loc": [20, 20]}],
        expected=[{"_id": 1, "loc": [10, 10]}],
        msg="Should match point at center (distance=0)",
    ),
    QueryTestCase(
        id="longitude_latitude_ordering",
        filter={"loc": {"$geoWithin": {"$center": [[-74, 40], 1]}}},
        doc=[{"_id": 1, "loc": [-74, 40]}, {"_id": 2, "loc": [40, -74]}],
        expected=[{"_id": 1, "loc": [-74, 40]}],
        msg="Should use [x, y] ordering",
    ),
    QueryTestCase(
        id="includes_geojson_point_without_index",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 10]}}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should return both legacy and GeoJSON documents without 2d index",
    ),
    QueryTestCase(
        id="no_documents_inside",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 1]}}},
        doc=[{"_id": 1, "loc": [10, 10]}, {"_id": 2, "loc": [20, 20]}],
        expected=[],
        msg="Should return empty result when no documents match",
    ),
    QueryTestCase(
        id="boundary_points_count",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 1.5]}}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
            {"_id": 3, "loc": [0, 1]},
            {"_id": 4, "loc": [-1, 0]},
            {"_id": 5, "loc": [0, -1]},
            {"_id": 6, "loc": [2, 2]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
            {"_id": 3, "loc": [0, 1]},
            {"_id": 4, "loc": [-1, 0]},
            {"_id": 5, "loc": [0, -1]},
        ],
        msg="Should return exactly 5 points within radius 1.5",
    ),
    QueryTestCase(
        id="with_additional_field_predicate",
        filter={
            "loc": {"$geoWithin": {"$center": [[0, 0], 2]}},
            "type": "a",
        },
        doc=[
            {"_id": 1, "loc": [0, 0], "type": "a"},
            {"_id": 2, "loc": [1, 0], "type": "b"},
            {"_id": 3, "loc": [0, 1], "type": "a"},
            {"_id": 4, "loc": [10, 10], "type": "a"},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0], "type": "a"},
            {"_id": 3, "loc": [0, 1], "type": "a"},
        ],
        msg="Should filter by both $center and additional field predicate",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_center_core_functionality(collection, test):
    """Verifies $center returns correct documents within the circular region."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
