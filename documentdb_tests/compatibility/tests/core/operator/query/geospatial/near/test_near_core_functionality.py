"""Tests for $near core functionality — nearest-first sorting, query interactions, nested fields."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

GEOJSON_CORE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_nearest_first",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Should return documents sorted nearest to farthest",
    ),
]

VALID_INTERACTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_inside_and",
        filter={
            "$and": [
                {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
                {"category": "A"},
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "category": "B"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "category": "A"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "category": "A"},
        ],
        msg="Should work inside $and with additional filter",
    ),
    QueryTestCase(
        id="near_with_equality_other_field",
        filter={
            "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
            "category": "A",
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "category": "B"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
        ],
        msg="Should combine with equality on another field",
    ),
]


@pytest.mark.usefixtures("geo_2dsphere")
@pytest.mark.parametrize(
    "test",
    pytest_params(GEOJSON_CORE_TESTS + VALID_INTERACTION_TESTS),
)
def test_near_core(collection, test):
    """Verifies $near core functionality."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


@pytest.mark.usefixtures("geo_2dsphere")
def test_near_explicit_sort_overrides_distance(collection):
    """Verifies explicit sort overrides $near distance ordering."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "rank": 3},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "rank": 1},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "rank": 2},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
            "sort": {"rank": 1},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "rank": 1},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "rank": 2},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "rank": 3},
        ],
        msg="Should sort by explicit field, overriding distance",
    )


def test_near_nested_field(collection):
    """Verifies $near works on nested field path."""
    collection.create_index([("address.location", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "address": {"location": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "address": {"location": {"type": "Point", "coordinates": [5, 5]}}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "address.location": {
                    "$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}
                }
            },
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "address": {"location": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "address": {"location": {"type": "Point", "coordinates": [5, 5]}}},
        ],
        msg="Should work on nested field path",
    )
