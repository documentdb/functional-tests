"""Tests for interactions between sibling geospatial operators."""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_nearSphere_with_geoWithin_on_another_field(collection):
    """Verifies $nearSphere on one field combined with $geoWithin on another."""
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
                "loc": {"type": "Point", "coordinates": [1, 1]},
                "loc2": {"type": "Point", "coordinates": [50, 50]},
            },
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
                "loc2": {"$geoWithin": {"$centerSphere": [[10, 10], 0.01]}},
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
        ],
        msg="Should combine $nearSphere on one field with $geoWithin on another",
    )


def test_near_combined_with_geowithin_different_field(collection):
    """Verifies $near on one field combined with $geoWithin on another field."""
    collection.create_index([("loc1", "2dsphere")])
    collection.create_index([("loc2", "2dsphere")])
    collection.insert_many(
        [
            {
                "_id": 1,
                "loc1": {"type": "Point", "coordinates": [0, 0]},
                "loc2": {"type": "Point", "coordinates": [10, 10]},
            },
            {
                "_id": 2,
                "loc1": {"type": "Point", "coordinates": [1, 1]},
                "loc2": {"type": "Point", "coordinates": [50, 50]},
            },
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc1": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
                "loc2": {
                    "$geoWithin": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[5, 5], [15, 5], [15, 15], [5, 15], [5, 5]]],
                        }
                    }
                },
            },
        },
    )
    assertSuccess(
        result,
        [
            {
                "_id": 1,
                "loc1": {"type": "Point", "coordinates": [0, 0]},
                "loc2": {"type": "Point", "coordinates": [10, 10]},
            }
        ],
        msg="Should filter by $geoWithin on loc2 while ordering by $near on loc1",
    )
