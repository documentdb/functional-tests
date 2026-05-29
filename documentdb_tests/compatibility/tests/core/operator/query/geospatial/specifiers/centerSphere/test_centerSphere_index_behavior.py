"""Tests for $centerSphere index behavior — 2dsphere, 2d, and no index."""

from documentdb_tests.compatibility.tests.core.operator.query.geospatial.utils.constants import (
    EARTH_RADIUS_KM,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_centerSphere_without_index(collection):
    """Verifies $centerSphere works without any geospatial index."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 200 / EARTH_RADIUS_KM]}}},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        ignore_doc_order=True,
        msg="Should return correct results without any index",
    )


def test_centerSphere_with_2dsphere_index(collection):
    """Verifies $centerSphere works with 2dsphere index."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 200 / EARTH_RADIUS_KM]}}},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        ignore_doc_order=True,
        msg="Should return same results with 2dsphere index",
    )


def test_centerSphere_with_2d_index(collection):
    """Verifies $centerSphere works with 2d index on legacy coordinates."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 1]},
            {"_id": 3, "loc": [50, 50]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 200 / EARTH_RADIUS_KM]}}},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 1]},
        ],
        ignore_doc_order=True,
        msg="Should return correct results with 2d index",
    )
