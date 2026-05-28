"""Tests for $near index behavior — index requirements, compound indexes, trailing fields."""

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import NO_QUERY_EXECUTION_PLANS_ERROR
from documentdb_tests.framework.executor import execute_command


def test_near_geojson_without_2dsphere_index_errors(collection):
    """Verifies $near GeoJSON fails without 2dsphere index when documents exist."""
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        },
    )
    assertFailureCode(
        result, NO_QUERY_EXECUTION_PLANS_ERROR, msg="Should error without 2dsphere index"
    )


def test_near_legacy_without_2d_index_errors(collection):
    """Verifies $near legacy fails without 2d index when documents exist."""
    collection.insert_one({"_id": 1, "loc": [0, 0]})
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$near": [0, 0]}}},
    )
    assertFailureCode(result, NO_QUERY_EXECUTION_PLANS_ERROR, msg="Should error without 2d index")


def test_near_geojson_with_only_2d_index_errors(collection):
    """Verifies $near GeoJSON fails with only 2d index (needs 2dsphere)."""
    collection.create_index([("loc", "2d")])
    collection.insert_one({"_id": 1, "loc": [0, 0]})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        },
    )
    assertFailureCode(
        result, NO_QUERY_EXECUTION_PLANS_ERROR, msg="Should error with only 2d index for GeoJSON"
    )


def test_near_with_compound_index(collection):
    """Verifies $near works with compound index including geo field."""
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
                "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
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


def test_near_2d_with_trailing_field_exists(collection):
    """Verifies $near with 2d index and $exists on trailing field."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0], "extra": "value"},
            {"_id": 2, "loc": [1, 1]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": [0, 0]}, "extra": {"$exists": True}},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0], "extra": "value"}],
        msg="Should filter by $exists on trailing field",
    )


def test_near_2d_with_trailing_field_null(collection):
    """Verifies $near with 2d index and null check on trailing field."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0], "extra": "value"},
            {"_id": 2, "loc": [1, 1]},
            {"_id": 3, "loc": [0.5, 0.5], "extra": None},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": [0, 0]}, "extra": None},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 3, "loc": [0.5, 0.5], "extra": None},
            {"_id": 2, "loc": [1, 1]},
        ],
        msg="Should match documents where trailing field is null or missing",
    )


def test_near_2d_with_trailing_field_not_exists(collection):
    """Verifies $near with 2d index and $exists:false on trailing field."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0], "extra": "value"},
            {"_id": 2, "loc": [1, 1]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": [0, 0]}, "extra": {"$exists": False}},
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "loc": [1, 1]}],
        msg="Should match documents where trailing field does not exist",
    )


def test_near_legacy_with_2dsphere_index(collection):
    """Verifies legacy $near fails when only 2dsphere index exists."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$near": [0, 0]}}},
    )
    assertFailureCode(
        result,
        NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Legacy $near should fail with only 2dsphere index",
    )


def test_near_multiple_2dsphere_indexes(collection):
    """Verifies $near selects correct index with multiple 2dsphere indexes."""
    collection.create_index([("loc1", "2dsphere")])
    collection.create_index([("loc2", "2dsphere")])
    collection.insert_many(
        [
            {
                "_id": 1,
                "loc1": {"type": "Point", "coordinates": [0, 0]},
                "loc2": {"type": "Point", "coordinates": [50, 50]},
            },
            {
                "_id": 2,
                "loc1": {"type": "Point", "coordinates": [5, 5]},
                "loc2": {"type": "Point", "coordinates": [0, 0]},
            },
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc1": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0]},
                        "$maxDistance": 1000000,
                    }
                }
            },
        },
    )
    assertSuccess(
        result,
        [
            {
                "_id": 1,
                "loc1": {"type": "Point", "coordinates": [0, 0]},
                "loc2": {"type": "Point", "coordinates": [50, 50]},
            },
            {
                "_id": 2,
                "loc1": {"type": "Point", "coordinates": [5, 5]},
                "loc2": {"type": "Point", "coordinates": [0, 0]},
            },
        ],
        msg="Should use loc1 index and order by distance from loc1",
    )
