"""Tests for $center index behavior — 2d index interaction, index bounds, and configuration."""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_center_with_2d_index_same_results(collection):
    """Test $center with 2d index returns same results as without index."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 1]},
            {"_id": 3, "loc": [10, 10]},
        ]
    )
    collection.create_index([("loc", "2d")])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 2]}}}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 1]}],
        msg="Should return same results with 2d index",
    )


def test_center_with_2d_index_custom_bounds(collection):
    """Test $center with 2d index using custom min/max bounds."""
    collection.create_index([("loc", "2d")], min=-500, max=500)
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [100, 100]},
            {"_id": 3, "loc": [400, 400]},
        ]
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 150]}}}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [100, 100]}],
        msg="Should work with custom 2d index bounds",
    )


def test_center_radius_at_full_index_bounds(collection):
    """Test $center with radius at full index bounds returns documents."""
    collection.create_index([("loc", "2d")], min=-100, max=100)
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
            {"_id": 3, "loc": [-50, -50]},
        ]
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [50, 50]}, {"_id": 3, "loc": [-50, -50]}],
        ignore_doc_order=True,
        msg="Should return documents within radius at full index bounds",
    )


def test_center_off_center_large_radius(collection):
    """Test $center with off-center point and large radius returns documents."""
    collection.create_index([("loc", "2d")], min=-100, max=100)
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
            {"_id": 3, "loc": [99, 99]},
        ]
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$center": [[50, 50], 80]}}}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [50, 50]}, {"_id": 3, "loc": [99, 99]}],
        ignore_doc_order=True,
        msg="Should return documents with off-center large radius",
    )


def test_center_with_2dsphere_index_not_supported(collection):
    """Test $center behavior with 2dsphere index — falls back to collection scan."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ]
    )
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}}},
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        ignore_doc_order=True,
        msg="Should work with 2dsphere index (falls back to collection scan)",
    )


def test_center_outside_2d_index_bounds(collection):
    """Test $center query with center outside 2d index bounds."""
    collection.create_index([("loc", "2d")], min=-100, max=100)
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$center": [[200, 200], 300]}}},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [50, 50]}],
        ignore_doc_order=True,
        msg="Should handle center outside 2d index bounds",
    )


def test_center_compound_2d_index(collection):
    """Test $center with compound index {loc: '2d', status: 1}."""
    collection.create_index([("loc", "2d"), ("status", 1)])
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0], "status": "active"},
            {"_id": 2, "loc": [1, 1], "status": "inactive"},
            {"_id": 3, "loc": [0, 0], "status": "inactive"},
            {"_id": 4, "loc": [50, 50], "status": "active"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$geoWithin": {"$center": [[0, 0], 5]}},
                "status": "active",
            },
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0], "status": "active"}],
        ignore_doc_order=True,
        msg="Should work with compound 2d index filtering on both geo and non-geo fields",
    )
