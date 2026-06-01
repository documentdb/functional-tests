"""Tests for $nearSphere index behavior — index requirements, compound, sparse indexes."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

LEGACY_COORDS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="2dsphere_index_legacy_coords",
        filter={"loc": {"$nearSphere": [0, 0]}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [5, 5]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [5, 5]},
        ],
        msg="Should succeed with 2dsphere index and legacy coordinates",
    ),
]


SUCCESS_TESTS: list[QueryTestCase] = LEGACY_COORDS_TESTS


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_nearSphere_index_success(collection, test):
    """Verifies $nearSphere succeeds with appropriate geo index."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_nearSphere_with_compound_index(collection):
    """Verifies $nearSphere works with compound index including geo field."""
    collection.create_index([("loc", "2dsphere"), ("category", 1)])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "category": "B"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "category": "A"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
                "category": "A",
            },
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "category": "A"},
        ],
        msg="Should filter by additional field with compound index",
    )


def test_nearSphere_with_multiple_2dsphere_indexes(collection):
    """Verifies $nearSphere works with multiple 2dsphere indexes on different fields."""
    collection.create_index([("loc", "2dsphere")])
    collection.create_index([("loc2", "2dsphere")])
    collection.insert_many(
        [
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "loc2": {"type": "Point", "coordinates": [10, 10]},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [5, 5]},
                "loc2": {"type": "Point", "coordinates": [0, 0]},
            },
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
            },
        },
    )
    assertSuccess(
        result,
        [
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "loc2": {"type": "Point", "coordinates": [10, 10]},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [5, 5]},
                "loc2": {"type": "Point", "coordinates": [0, 0]},
            },
        ],
        msg="Should work with multiple 2dsphere indexes on different fields",
    )


def test_nearSphere_with_sparse_index(collection):
    """Verifies $nearSphere works with sparse 2dsphere index."""
    collection.create_index([("loc", "2dsphere")], sparse=True)
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "name": "no location"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
            },
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        msg="Should work with sparse 2dsphere index, skipping docs without field",
    )
