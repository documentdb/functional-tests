"""Tests for interaction between $minDistance and $maxDistance ($near, 2dsphere index)."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ORIGIN = {"type": "Point", "coordinates": [0, 0]}


INTERACTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="min_less_than_max_normal",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 100000,
                    "$maxDistance": 500000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 2]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 2]}},
        ],
        msg="Should return docs in annular region when $minDistance < $maxDistance",
    ),
    QueryTestCase(
        id="min_greater_than_max_empty",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 500000,
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 2]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        expected=[],
        msg="Should return empty when $minDistance > $maxDistance",
    ),
    QueryTestCase(
        id="min_equals_max",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 500000,
                    "$maxDistance": 500000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [3, 3]}},
        ],
        expected=[],
        msg="Should return empty (or exact distance match) when $minDistance = $maxDistance",
    ),
    QueryTestCase(
        id="min_zero_same_as_max_alone",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 0,
                    "$maxDistance": 200000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        msg="Should behave same as $maxDistance alone when $minDistance is 0",
    ),
    QueryTestCase(
        id="both_zero",
        filter={
            "loc": {
                "$near": {
                    "$geometry": ORIGIN,
                    "$minDistance": 0,
                    "$maxDistance": 0,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should return only exact match when both $minDistance and $maxDistance are 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INTERACTION_TESTS))
def test_minmax_distance_interaction(collection, test):
    """Verifies $minDistance + $maxDistance interaction with $near and GeoJSON geometry."""
    collection.create_index([("loc", "2dsphere")])
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
